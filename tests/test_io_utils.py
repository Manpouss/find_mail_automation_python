# tests/test_io_utils.py
from __future__ import annotations

from pathlib import Path

import pandas as pd

from enricher.io_utils import detect_delimiter, read_csv_robust, ensure_columns, write_csv_safe


def test_detect_delimiter_semicolon(tmp_path: Path):
    p = tmp_path / "a.csv"
    p.write_text("col1;col2\n1;2\n", encoding="utf-8")
    assert detect_delimiter(p, encoding="utf-8") == ";"


def test_read_csv_robust_with_explicit_sep(tmp_path: Path):
    p = tmp_path / "b.csv"
    p.write_text("a;b\nx;y\n", encoding="utf-8")
    df, sep = read_csv_robust(p, in_sep=";", encoding="utf-8-sig")
    assert sep == ";"
    assert list(df.columns) == ["a", "b"]
    assert df.iloc[0]["a"] == "x"


def test_read_csv_robust_encoding_fallback_cp1252(tmp_path: Path):
    # Contains 'é' which is common in cp1252
    content = "a;b\ncafé;ok\n"
    p = tmp_path / "c.csv"
    p.write_bytes(content.encode("cp1252"))

    df, sep = read_csv_robust(p, in_sep=";", encoding="utf-8-sig")
    assert sep == ";"
    assert df.iloc[0]["a"] == "café"


def test_ensure_columns_adds_expected_columns():
    df = pd.DataFrame({"x": ["1"]})
    df2 = ensure_columns(df)
    for col in ("email", "source_url", "method", "status", "confidence", "external_urls", "primary_domain", "discovery_source"):
        assert col in df2.columns
    assert df2.loc[0, "status"] == "not_processed"


def test_write_csv_safe_creates_file(tmp_path: Path):
    df = pd.DataFrame({"a": ["1"], "b": ["2"]})
    out = tmp_path / "out.csv"
    p = write_csv_safe(df, out, sep=";")
    assert p.exists()
    text = p.read_text(encoding="utf-8-sig")
    assert "a" in text and "b" in text
