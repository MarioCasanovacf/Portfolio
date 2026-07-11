#!/usr/bin/env python3
"""Download and prepare the Multilingual Amazon Reviews Corpus.

Usage:
    python download_data.py              # Download full dataset + sample
    python download_data.py --sample-only # Generate sample from already-downloaded data

The script is idempotent: re-running it will skip already-downloaded files.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve project paths relative to this script's location
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
FULL_DIR = DATA_DIR / "full"

LANGUAGES = ["en", "de", "es", "fr", "ja", "zh"]
SAMPLE_PER_LANG = 1000
SEED = 42


def download_full_dataset():
    """Download the full MARC dataset from HuggingFace Hub."""
    try:
        from datasets import load_dataset
    except ImportError:
        print(
            "ERROR: 'datasets' package not installed. Run:\n"
            "  pip install datasets",
            file=sys.stderr,
        )
        sys.exit(1)

    FULL_DIR.mkdir(parents=True, exist_ok=True)

    for lang in LANGUAGES:
        out_path = FULL_DIR / f"reviews_{lang}.csv"
        if out_path.exists():
            print(f"  [skip] {out_path.name} already exists")
            continue

        print(f"  [download] {lang}...", end=" ", flush=True)
        ds = load_dataset("goosmanlei/amazon_reviews_multi", lang, split="train")
        df = ds.to_pandas()
        df.to_csv(out_path, index=False)
        print(f"{len(df):,} rows")

    # Also download test split (we use this as frozen test set)
    for lang in LANGUAGES:
        out_path = FULL_DIR / f"reviews_{lang}_test.csv"
        if out_path.exists():
            print(f"  [skip] {out_path.name} already exists")
            continue

        print(f"  [download] {lang} test...", end=" ", flush=True)
        ds = load_dataset("goosmanlei/amazon_reviews_multi", lang, split="test")
        df = ds.to_pandas()
        df.to_csv(out_path, index=False)
        print(f"{len(df):,} rows")

    print("Full dataset ready.")


def create_sample():
    """Create a small stratified sample for the committed repo."""
    import pandas as pd

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    for lang in LANGUAGES:
        full_path = FULL_DIR / f"reviews_{lang}.csv"
        out_path = SAMPLE_DIR / f"reviews_{lang}_sample.csv"

        if not full_path.exists():
            print(f"  [warn] {full_path.name} not found — run without --sample-only first")
            continue

        df = pd.read_csv(full_path)
        # Stratified sample by star rating
        sample = df.groupby("stars", group_keys=False).apply(
            lambda x: x.sample(
                n=min(SAMPLE_PER_LANG // 5, len(x)),
                random_state=SEED,
            )
        )
        sample.to_csv(out_path, index=False)
        print(f"  [sample] {lang}: {len(sample):,} rows -> {out_path.name}")

    print("Sample ready.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample-only",
        action="store_true",
        help="Only regenerate the sample from already-downloaded data",
    )
    args = parser.parse_args()

    if not args.sample_only:
        print("Downloading full Multilingual Amazon Reviews Corpus...")
        download_full_dataset()

    print("Creating committed sample...")
    create_sample()

    print("\nDone.")


if __name__ == "__main__":
    main()
