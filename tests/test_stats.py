# tests/test_stats.py
from __future__ import annotations

import pandas as pd

from enricher.stats import compute_stats, format_stats


def test_compute_stats_counts_correctly():
    df = pd.DataFrame(
        {
            "status": ["found", "found", "not_found", "blocked", "found"],
            "method": ["detected_emails", "crawl", "", "", "bio_text"],
            "external_urls": ["", "https://a.com", "", "https://b.com", ""],
        }
    )

    s = compute_stats(df)
    assert s.total_rows == 5
    assert s.found_total == 3
    assert s.found_local == 2
    assert s.found_crawl == 1
    assert s.blocked == 1
    assert s.not_found == 1
    assert s.prepared_with_external_urls == 2
    assert s.recovery_rate_pct() == 60.0


def test_format_stats_contains_key_lines():
    df = pd.DataFrame(
        {
            "status": ["found", "not_found"],
            "method": ["crawl", ""],
            "external_urls": ["https://a.com", ""],
        }
    )
    s = compute_stats(df)
    txt = format_stats(s)
    assert "Run Summary" in txt
    assert "Total rows" in txt
    assert "Found (total)" in txt
