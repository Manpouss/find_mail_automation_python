# enricher/stats.py
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class RunStats:
    total_rows: int
    found_total: int
    found_local: int
    found_crawl: int
    blocked: int
    not_found: int
    prepared_with_external_urls: int

    def recovery_rate_pct(self) -> float:
        if self.total_rows <= 0:
            return 0.0
        return round((self.found_total / self.total_rows) * 100.0, 2)


def compute_stats(df: pd.DataFrame) -> RunStats:
    """
    Compute execution stats from the enriched dataframe.
    Requires at least columns: status, method, external_urls.
    """
    total = len(df)

    def _count(mask) -> int:
        try:
            return int(mask.sum())
        except Exception:
            return 0

    status = df["status"] if "status" in df.columns else pd.Series([""] * total)
    method = df["method"] if "method" in df.columns else pd.Series([""] * total)
    external_urls = df["external_urls"] if "external_urls" in df.columns else pd.Series([""] * total)

    found_total = _count(status == "found")
    blocked = _count(status == "blocked")
    not_found = _count(status == "not_found")

    found_local = _count((status == "found") & (method.isin(["detected_emails", "bio_text"])))
    found_crawl = _count((status == "found") & (method == "crawl"))

    prepared = _count(external_urls.astype(str).str.len() > 0)

    return RunStats(
        total_rows=total,
        found_total=found_total,
        found_local=found_local,
        found_crawl=found_crawl,
        blocked=blocked,
        not_found=not_found,
        prepared_with_external_urls=prepared,
    )


def format_stats(stats: RunStats) -> str:
    """
    Create a human-readable summary.
    """
    return (
        "=== Run Summary ===\n"
        f"Total rows: {stats.total_rows}\n"
        f"Found (total): {stats.found_total} ({stats.recovery_rate_pct()}%)\n"
        f"  - Found (local): {stats.found_local}\n"
        f"  - Found (crawl): {stats.found_crawl}\n"
        f"Prepared with external URLs: {stats.prepared_with_external_urls}\n"
        f"Blocked (403/429): {stats.blocked}\n"
        f"Not found: {stats.not_found}\n"
    )
