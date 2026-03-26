"""
run_pipeline.py
---------------
Executes the full data preparation pipeline and saves the result to data/clean/.

  Step 1 — data_ingest          : Load raw CSV from data/raw/
  Step 2 — data_quality         : Extract surface, validate constraints
  Step 3 — data_cleaner         : Rename columns, clean & impute, hash contacts
  Step 4 — feature_engineering  : Outliers, target encoding, log(prix), one-hot
  Step 5 — Save                 : Write ML-ready CSV to data/clean/

Usage (from project root):
  python src/run_pipeline.py                    # uses latest CSV in data/raw/
  python src/run_pipeline.py ads_export.csv     # uses a specific file
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Make sure the project root is on the Python path when running as a script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features.data_ingest import load_raw
from src.features.data_quality import data_quality
from src.features.data_cleaner import clean_leboncoin_data
from src.features.feature_engineering import engineer_features

# ---------------------------------------------------------------------------
CLEAN_DIR = ROOT / "data" / "clean"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
# ---------------------------------------------------------------------------


def run(filename: str = None) -> Path:
    """
    Run the four-step pipeline, save the ML-ready CSV to data/clean/,
    and return the path to the saved file.
    """

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
    log.info(f"  → {len(df_clean):,} rows, {len(df_clean.columns)} columns")
    log.info(f"  → Columns : {df_clean.columns.tolist()}")

    # ── Step 4: Feature Engineering ─────────────────────────────────────────
    log.info("Step 4 — Features  : outliers, target encoding, log(prix), one-hot …")
    df_features = engineer_features(df_clean)
    log.info(f"  → {len(df_features):,} rows, {len(df_features.columns)} columns (ML-ready)")
    log.info(f"  → Columns : {df_features.columns.tolist()}")

    # ── Step 5: Save to data/clean/ ─────────────────────────────────────────
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    out_path = CLEAN_DIR / f"{timestamp}_clean.csv"
    df_features.to_csv(out_path)
    log.info(f"Step 5 — Saved     : {out_path.relative_to(ROOT)}")

    # ── Summary ─────────────────────────────────────────────────────────────
    log.info("Pipeline finished ✓")
    print("\n── Sample output (first 5 rows) ──────────────────────────────────")
    print(df_features.head().to_string())
    print()

    return out_path


if __name__ == "__main__":
    # Optional: pass a filename as a command-line argument
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    saved = run(csv_file)
    print(f"✓ ML-ready data saved to: {saved}")
