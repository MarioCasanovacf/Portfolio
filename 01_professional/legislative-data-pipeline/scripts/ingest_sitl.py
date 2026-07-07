"""Ingest SITL per-deputy roll-call captures into the raw DuckDB layer.

Loads the CSVs the SITL scraper (and `backfill_sitl_meta.py`) produced for every
captured legislature under `data/raw/sitl/{slug}/`:

  - sitl_votes_{slug}.csv      -> raw.raw_sitl_votes      (one row per deputy per vote)
  - sitl_vote_meta_{slug}.csv  -> raw.raw_sitl_vote_meta  (one row per vote: date, title)
  - sitl_tallies_{slug}.csv    -> raw.raw_sitl_tallies    (official per-party tallies)

NO network. Idempotent (CREATE OR REPLACE) and ADDITIVE — it does not touch the
dipMex tables. Documented flow:

    python scripts/ingest_dipmex.py   # builds the DB + dipMex raw (downloads from GitHub)
    python scripts/ingest_sitl.py     # adds the SITL raw from local CSVs
    cd dbt_project && dbt build
"""

from __future__ import annotations

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "legislative.duckdb"
SITL_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "sitl"


def _union_csv(glob_pat: str) -> str | None:
    """UNION (by column name) every CSV matching the glob, or None if there are none."""
    files = sorted(SITL_DIR.glob(glob_pat))
    if not files:
        return None
    def rd(p: Path) -> str:
        return f"read_csv_auto('{p.as_posix()}', header=true, all_varchar=true, sample_size=-1)"
    return " UNION ALL BY NAME ".join(f"SELECT * FROM {rd(f)}" for f in files)


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    specs = {
        "raw_sitl_votes": "*/sitl_votes_*.csv",
        "raw_sitl_vote_meta": "*/sitl_vote_meta_*.csv",
        "raw_sitl_tallies": "*/sitl_tallies_*.csv",
    }
    for table, pat in specs.items():
        sql = _union_csv(pat)
        if sql is None:
            print(f"  (no files for raw.{table}; skipped)")
            continue
        con.execute(f"CREATE OR REPLACE TABLE raw.{table} AS {sql}")
        n = con.sql(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
        print(f"  raw.{table:<22} {n:>8,} rows")
    print("\n[+] SITL raw landed in", DB_PATH)
    con.close()


if __name__ == "__main__":
    main()
