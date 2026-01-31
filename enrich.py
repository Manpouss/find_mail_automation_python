# enrich.py
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from enricher.io_utils import read_csv_robust, ensure_columns, write_csv_safe
from enricher.extractors import enrich_row_local
from enricher.discovery import DiscoveryConfig, discover_external_urls_from_row
from enricher.urls import get_domain
from enricher.crawler import crawl_for_email
from enricher.stats import compute_stats, format_stats
from enricher.io_utils import read_csv_robust, ensure_columns, write_csv_safe
from enricher.extractors import enrich_row_local
from enricher.crawler import crawl_for_email



def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CSV email enricher (public-only, controlled discovery).")
    p.add_argument("input_csv", help="Path to input CSV")
    p.add_argument("-o", "--output", default=None, help="Output path (default: <input>_enriched.csv)")
    p.add_argument("--in-sep", default=None, help="Input delimiter (auto if omitted)")
    p.add_argument("--out-sep", default=None, help="Output delimiter (defaults to input delimiter)")
    p.add_argument("--encoding", default="utf-8-sig", help="Input encoding (default utf-8-sig)")

    # performance + safety
    p.add_argument("--max-urls-per-row", type=int, default=2, help="Max external URLs retained per row (default 2)")
    p.add_argument("--timeout", type=int, default=10, help="HTTP timeout seconds (default 10)")
    p.add_argument("--max-pages", type=int, default=3, help="Max pages per domain (default 3)")
    p.add_argument("--no-crawl", action="store_true", help="Disable website crawling (local extraction + discovery only)")
    p.add_argument("--print-urls", action="store_true", help="Print unique detected external URLs")
    p.add_argument("--limit-rows", type=int, default=0, help="Process only first N rows (debug). 0 = all")

    return p


def _safe_get(df: pd.DataFrame, idx: int, col: str) -> str:
    if col in df.columns:
        return str(df.at[idx, col] or "")
    return ""


def main() -> None:
    args = build_arg_parser().parse_args()

    input_path = Path(args.input_csv)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    # 1) Read CSV robustly
    df, in_sep = read_csv_robust(input_path, args.in_sep, args.encoding)
    if len(df.columns) == 0:
        raise SystemExit("Input CSV has no columns. Please provide a valid CSV with headers.")

    df = ensure_columns(df)

    # Optional debug limit
    if args.limit_rows and args.limit_rows > 0:
        df = df.head(args.limit_rows).copy()

    print(f"Loaded {len(df)} rows from {input_path.name} (in-sep='{in_sep}')")

    # 2) Local enrichment: detected_emails -> bio_text
    found_local = 0
    for idx in range(len(df)):
        if df.at[idx, "status"] != "not_processed":
            continue

        bio = _safe_get(df, idx, "bio_text")
        det = _safe_get(df, idx, "detected_emails")

        email, src, method, status, conf = enrich_row_local(bio, det)

        df.at[idx, "email"] = email
        df.at[idx, "source_url"] = src
        df.at[idx, "method"] = method
        df.at[idx, "status"] = status
        df.at[idx, "confidence"] = conf

        if status == "found":
            found_local += 1

    print(f"Local enrichment done. Found emails on {found_local}/{len(df)} rows.")

    # 3) Controlled public discovery: build external_urls from multiple fields
    cfg = DiscoveryConfig(
    field_priority=("bio_links", "bio_text", "description"),
    max_urls_per_row=args.max_urls_per_row,
    exclude_low_value=True,
    )

    prepared = 0
    for idx in range(len(df)):
        if df.at[idx, "status"] != "not_found":
            continue

        row_map = {
            "bio_links": df.at[idx, "bio_links"] if "bio_links" in df.columns else "",
            "bio_text": df.at[idx, "bio_text"] if "bio_text" in df.columns else "",
            "description": df.at[idx, "description"] if "description" in df.columns else "",
        }

        urls, src_field = discover_external_urls_from_row(row_map, cfg)

        if urls:
            df.at[idx, "external_urls"] = "|".join(urls)
            df.at[idx, "primary_domain"] = get_domain(urls[0])
            df.at[idx, "discovery_source"] = src_field
            prepared += 1
        else:
            df.at[idx, "discovery_source"] = "none"

    print(f"External URL discovery done. Prepared {prepared} rows with external_urls.")


    # 4) Optional: print unique external URLs
    if args.print_urls:
        unique = set()
        for idx in range(len(df)):
            ext = str(df.at[idx, "external_urls"] or "")
            if not ext:
                continue
            for u in ext.split("|"):
                u = u.strip()
                if u:
                    unique.add(u)

        print("\nDetected external URLs:")
        for u in sorted(unique):
            print("-", u)
        print(f"\nTotal unique external URLs: {len(unique)}")

    # 5) Crawl (Option A): only crawl discovered external URLs, limited by max_pages
    crawled_found = crawled_blocked = crawled_errors = 0
    if not args.no_crawl:
        for idx in range(len(df)):
            if df.at[idx, "status"] != "not_found":
                continue

            ext = str(df.at[idx, "external_urls"] or "")
            if not ext:
                continue

            urls = [u.strip() for u in ext.split("|") if u.strip()]
            for u in urls:
                email, src, st, conf = crawl_for_email(u, timeout=args.timeout, max_pages=args.max_pages)

                if st == "found":
                    df.at[idx, "email"] = email
                    df.at[idx, "source_url"] = src
                    df.at[idx, "method"] = "crawl"
                    df.at[idx, "status"] = "found"
                    df.at[idx, "confidence"] = conf
                    crawled_found += 1
                    break

                if st == "blocked":
                    crawled_blocked += 1

                if st == "error":
                    crawled_errors += 1

        print(
            f"Crawl done. Newly found emails: {crawled_found} | blocked: {crawled_blocked} | errors: {crawled_errors}"
        )
    else:
        print("Crawl skipped (--no-crawl).")

    # 6) Write output
    out_sep = args.out_sep or in_sep
    out_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "_enriched.csv")
    out_path = write_csv_safe(df, out_path, sep=out_sep)
    print(f"Output written to {out_path.name} (out-sep='{out_sep}')")

    # 7) Print stats summary
    stats = compute_stats(df)
    print(format_stats(stats))


if __name__ == "__main__":
    main()
