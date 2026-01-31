# tests/test_enrich_integration.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

import enrich as enrich_module


def test_pipeline_discovers_url_outside_bio_links_and_crawls(monkeypatch, tmp_path: Path):
    # 1) create input CSV (no bio_links)
    df = pd.DataFrame(
        {
            "bio_links": ["", ""],
            "bio_text": ["my website is www.example.com", ""],
            "description": ["", "reach us at mybusiness.fr/contact"],
            "detected_emails": ["", ""],
        }
    )

    input_csv = tmp_path / "input.csv"
    df.to_csv(input_csv, index=False, encoding="utf-8-sig", sep=",")

    # 2) monkeypatch crawl_for_email to avoid real HTTP
    def fake_crawl(url: str, timeout: int = 10, max_pages: int = 3):
        if "example.com" in url:
            return "hello@realcompany.com", "https://www.example.com/contact", "found", "0.6"
        if "mybusiness.fr" in url:
            return "contact@mybusiness.fr", "https://mybusiness.fr/contact", "found", "0.6"
        return "", "", "not_found", ""

    monkeypatch.setattr(enrich_module, "crawl_for_email", fake_crawl)

    # 3) run main() with args
    out_csv = tmp_path / "out.csv"
    argv = [
        "enrich.py",
        str(input_csv),
        "--in-sep",
        ",",
        "--out-sep",
        ",",
        "-o",
        str(out_csv),
        "--max-pages",
        "1",
        "--timeout",
        "1",
    ]

    monkeypatch.setattr("sys.argv", argv)

    enrich_module.main()

    # 4) validate output
    out = pd.read_csv(out_csv, encoding="utf-8-sig", sep=",", dtype=str, keep_default_na=False)

    assert "external_urls" in out.columns
    assert "discovery_source" in out.columns
    assert out.loc[0, "discovery_source"] in ("bio_text", "description")
    assert "example.com" in out.loc[0, "external_urls"]
    assert out.loc[0, "email"] == "hello@realcompany.com"

    assert "mybusiness.fr" in out.loc[1, "external_urls"]
    assert out.loc[1, "email"] == "contact@mybusiness.fr"
