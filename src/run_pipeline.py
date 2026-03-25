"""
run_pipeline.py
---------------
Executes the full data preparation pipeline:
  Step 1 — data_ingest   : Load raw CSV from data/raw/
  Step 2 — data_quality  : Extract surface, validate constraints
  Step 3 — data_cleaner  : Rename columns, clean & impute, hash contacts

Usage (from project root):
  python scripts/run_pipeline.py                    # uses latest CSV in data/raw/
  python scripts/run_pipeline.py ads_export.csv     # uses a specific file
"""

import sys
import os
import logging
from pathlib import Path

# Make sure the project root is on the Python path when running as a script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from features.data_ingest import load_raw
from features.data_quality import data_quality
from features.data_cleaner import clean_leboncoin_data

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


def run(filename: str = None) -> None:
    """Run the three-step pipeline and print a summary."""

    # ── Step 1: Ingest ──────────────────────────────────────────────────────
    log.info("Step 1 — Ingestion : loading raw CSV …")
    df_raw = load_raw(filename)
    log.info(f"  → {len(df_raw):,} rows, {len(df_raw.columns)} columns loaded")

    # ── Step 2: Quality ─────────────────────────────────────────────────────
    log.info("Step 2 — Quality   : extracting surface & applying constraints …")
    df_quality = data_quality(df_raw)
    dropped = len(df_raw) - len(df_quality)
    log.info(f"  → {len(df_quality):,} rows kept  ({dropped} dropped by quality checks)")

    # ── Step 3: Cleaning ────────────────────────────────────────────────────
    log.info("Step 3 — Cleaning  : renaming columns, imputing, hashing …")
    df_clean = clean_leboncoin_data(df_quality)
    log.info(f"  → {len(df_clean):,} rows, {len(df_clean.columns)} columns in final dataset")
    log.info(f"  → Columns : {df_clean.columns.tolist()}")

    # ── Summary ─────────────────────────────────────────────────────────────
    log.info("Pipeline finished ✓")
    print("\n── Sample output (first 5 rows) ──────────────────────────────────")
    print(df_clean.head().to_string())
    print()

    return df_clean


if __name__ == "__main__":
    # Optional: pass a filename as a command-line argument
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    run(csv_file)
