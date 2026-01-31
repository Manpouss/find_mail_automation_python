# enricher/io_utils.py
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd


def detect_delimiter(file_path: Path, encoding: str) -> str:
    """
    Detect CSV delimiter from the first bytes using csv.Sniffer.
    Falls back to comma.
    """
    try:
        sample = file_path.read_text(encoding=encoding, errors="replace")[:8192]
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        return ","


def read_csv_robust(input_path: Path, in_sep: str | None, encoding: str) -> Tuple[pd.DataFrame, str]:
    """
    Robust CSV reader:
    - delimiter detection if not provided
    - encoding fallbacks: utf-8-sig -> utf-8 -> cp1252 -> latin-1
    - fallback to python engine + skip bad lines for messy CSVs
    """
    used_sep = in_sep or detect_delimiter(input_path, encoding=encoding)
    read_kwargs = dict(sep=used_sep, dtype=str, keep_default_na=False)

    # 1) First try requested encoding
    try:
        df = pd.read_csv(input_path, encoding=encoding, **read_kwargs)
        return df, used_sep
    except pd.errors.EmptyDataError:
        print("Input CSV is empty (no columns). Please provide a file with headers.")
        sys.exit(1)
    except UnicodeDecodeError:
        pass
    except pd.errors.ParserError:
        # fallthrough
        pass
    except Exception:
        # fallthrough
        pass

    # 2) Encoding fallbacks (common in real CSVs)
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(input_path, encoding=enc, **read_kwargs)
            return df, used_sep
        except pd.errors.EmptyDataError:
            print("Input CSV is empty (no columns). Please provide a file with headers.")
            sys.exit(1)
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            continue
        except Exception:
            continue

    # 3) Last resort: python engine + skip bad lines
    try:
        df = pd.read_csv(
            input_path,
            encoding="latin-1",
            engine="python",
            on_bad_lines="skip",
            **read_kwargs,
        )
        print("Warning: CSV had malformed rows; some lines were skipped for successful parsing.")
        return df, used_sep
    except pd.errors.EmptyDataError:
        print("Input CSV is empty (no columns). Please provide a file with headers.")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to read CSV robustly: {e}")
        sys.exit(1)


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all output columns exist.
    We keep defaults empty; status defaults to not_processed.
    """
    columns_defaults = {
        "email": "",
        "source_url": "",
        "method": "",
        "status": "not_processed",
        "confidence": "",
        "external_urls": "",
        "primary_domain": "",
        "discovery_source": "",  # helpful for audit: bio_links / bio_text / description / none
    }
    for col, default in columns_defaults.items():
        if col not in df.columns:
            df[col] = default
    return df


def write_csv_safe(df: pd.DataFrame, output_path: Path, sep: str) -> Path:
    """
    Write CSV safely (Excel-friendly UTF-8 with BOM).
    - Quote all fields to keep separators inside text safe.
    - If file is open (PermissionError), write to timestamped alternative.
    """
    def _write(path: Path) -> None:
        df.to_csv(
            path,
            index=False,
            encoding="utf-8-sig",
            sep=sep,
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
        )

    try:
        _write(output_path)
        return output_path
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt = output_path.with_name(f"{output_path.stem}_{ts}{output_path.suffix}")
        print(f"Permission denied writing '{output_path.name}'. Writing to '{alt.name}' instead.")
        _write(alt)
        return alt
