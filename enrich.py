from __future__ import annotations

import argparse
from pathlib import Path

from enricher.io_utils import read_csv_robust, ensure_columns, write_csv_safe
from enricher.extractors import enrich_row_local
from enricher.urls import extract_urls_from_bio_links, filter_external_urls, get_domain
from enricher.crawler import crawl_for_email


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CSV email enricher (public-only).")
    p.add_argument("input_csv", help="Path to input CSV")
    p.add_argument("-o", "--output", default=None, help="Output path (default: <input>_enriched.csv)")
    p.add_argument("--in-sep", default=None, help="Input delimiter (auto if omitted)")
    p.add_argument("--out-sep", default=None, help="Output delimiter (defaults to input delimiter)")
    p.add_argument("--encoding", default="utf-8-sig", help="Input encoding (default utf-8-sig)")
    p.add_argument("--max-urls-per-row", type=int, default=2, help="Max external URLs per row (default 2)")
    p.add_argument("--timeout", type=int, default=10, help="HTTP timeout seconds (default 10)")
    p.add_argument("--max-pages", type=int, default=3, help="Max pages per domain (default 3)")
    p.add_argument("--no-crawl", action="store_true", help="Disable website crawling (local only)")
    p.add_argument("--print-urls", action="store_true", help="Print unique detected external URLs")
    return p


def main():
    args = build_arg_parser().parse_args()
    input_path = Path(args.input_csv)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df, in_sep = read_csv_robust(input_path, args.in_sep, args.encoding)
    if len(df.columns) == 0:
        raise SystemExit("Input CSV has no columns. Please provide a valid CSV with headers.")

    df = ensure_columns(df)
    print(f"Loaded {len(df)} rows from {input_path.name} (in-sep='{in_sep}')")

    # Step 4 — local enrichment
    found_local = 0
    for idx in range(len(df)):
        if df.at[idx, "status"] != "not_processed":
            continue
        bio = df.at[idx, "bio_text"] if "bio_text" in df.columns else ""
        det = df.at[idx, "detected_emails"] if "detected_emails" in df.columns else ""
        email, src, method, status, conf = enrich_row_local(bio, det)

        df.at[idx, "email"] = email
        df.at[idx, "source_url"] = src
        df.at[idx, "method"] = method
        df.at[idx, "status"] = status
        df.at[idx, "confidence"] = conf

        if status == "found":
            found_local += 1

    print(f"Local enrichment done. Found emails on {found_local}/{len(df)} rows.")

    # Step 5 — prepare external urls
    prepared = 0
    for idx in range(len(df)):
        if df.at[idx, "status"] != "not_found":
            continue

        bio_links = df.at[idx, "bio_links"] if "bio_links" in df.columns else ""
        urls = extract_urls_from_bio_links(bio_links)
        urls = filter_external_urls(urls, max_urls=args.max_urls_per_row, exclude_low_value=True)

        if urls:
            df.at[idx, "external_urls"] = "|".join(urls)
            df.at[idx, "primary_domain"] = get_domain(urls[0])
            prepared += 1

    print(f"External URL prep done. Prepared {prepared} rows with external_urls.")

    if args.print_urls:
        unique = set()
        for idx in range(len(df)):
            ext = df.at[idx, "external_urls"]
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

    # Step 6 — crawl light (Option A)
    crawled_found = crawled_blocked = 0
    if not args.no_crawl:
        for idx in range(len(df)):
            if df.at[idx, "status"] != "not_found":
                continue
            ext = df.at[idx, "external_urls"]
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

        print(f"Crawl light done. Newly found emails: {crawled_found} | blocked: {crawled_blocked}")

    out_sep = args.out_sep or in_sep
    out_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "_enriched.csv")
    out_path = write_csv_safe(df, out_path, sep=out_sep)
    print(f"Output written to {out_path.name} (out-sep='{out_sep}')")
    


if __name__ == "__main__":
    main()
