from __future__ import annotations

import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd


def detect_delimiter(file_path: Path, encoding: str) -> str:
    try:
        sample = file_path.read_text(encoding=encoding, errors="replace")[:8192]
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        return ","


def read_csv_robust(input_path: Path, in_sep: str | None, encoding: str) -> Tuple[pd.DataFrame, str]:
    used_sep = in_sep or detect_delimiter(input_path, encoding=encoding)
    read_kwargs = dict(sep=used_sep, dtype=str, keep_default_na=False)
    try:
        df = pd.read_csv(input_path, encoding=encoding, **read_kwargs)
    except UnicodeDecodeError:
        # Fallbacks common on Windows exports
        for enc in ("utf-8", "cp1252", "latin-1"):
            try:
                df = pd.read_csv(input_path, encoding=enc, **read_kwargs)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise
    except pd.errors.EmptyDataError:
        print("Input CSV is empty (no columns). Please provide a file with headers.")
        sys.exit(1)
    except Exception:
        df = pd.read_csv(
            input_path,
            encoding=encoding,
            engine="python",
            on_bad_lines="skip",
            **read_kwargs,
        )


    return df, used_sep


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all output columns exist.
    """
    columns_defaults = {
        "email": "",
        "source_url": "",
        "method": "",
        "status": "not_processed",
        "confidence": "",
        "external_urls": "",
        "primary_domain": "",
    }
    for col, default in columns_defaults.items():
        if col not in df.columns:
            df[col] = default
    return df


import csv

def write_csv_safe(df, output_path, sep):
    try:
        df.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
            sep=sep,
            quoting=csv.QUOTE_ALL,
            escapechar="\\"
        )
        return output_path
    except PermissionError:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt = output_path.with_name(f"{output_path.stem}_{ts}{output_path.suffix}")
        print(f"Permission denied writing '{output_path.name}'. Writing to '{alt.name}' instead.")
        df.to_csv(
            alt,
            index=False,
            encoding="utf-8-sig",
            sep=sep,
            quoting=csv.QUOTE_ALL,
            escapechar="\\"
        )
        return alt

