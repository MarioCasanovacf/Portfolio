"""Ingest REAL dipMex data into the raw DuckDB layer.

dipMex (github.com/emagar/dipMex) is a static, citable academic dataset — the
sustainable, reproducible backbone for this pipeline (no fragile live scraping).
It provides a COMPLETE roll-call record for legislatures **60 and 61**:

    data/votesForWeb/rc{60,61}.csv.zip  ->  three files each:
      - dipdat{leg}.csv  roster: id, party, name, nomregexp, and real seat
                         entry/exit dates split into yr/mo/dy columns.
      - votdat{leg}.csv  one row per vote event: title, date (yr/mo/dy), tallies.
      - rc{leg}.csv      the roll-call MATRIX: rows = vote events, columns = the
                         stable legislator `id` (ags01p, ags01s, ...). Cells are
                         vote codes (1 favor, 2 contra, 3 abstención, 5 ausente).

Because the matrix columns ARE the stable ids, votes join the dimension natively
by id — no name bridge needed for dipMex (the fuzzy bridge is for the SITL/recent
path, where votes carry only names).

Recent rosters (dip64/65/66.csv) are also landed — real, but dipMex has no
individual roll-calls for those legislatures, so they feed the dimension only.

Run:  python scripts/ingest_dipmex.py
Then: cd dbt_project && dbt build
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import duckdb

REPO = "https://raw.githubusercontent.com/emagar/dipMex/master/data"
ROLLCALL_LEGS = (60, 61)          # complete coverage: roster + votes
RECENT_ROSTER_LEGS = (64, 65, 66)  # roster only (real), votes not in dipMex
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "legislative.duckdb"
DL_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "dipmex"


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "MexLegislativePipeline/0.1 (academic)"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 (trusted host)
        dest.write_bytes(r.read())
    return dest


def _fetch_rollcall_bundle(leg: int) -> dict[str, Path]:
    """Download and extract dipdat/votdat/rc for one legislature."""
    url = f"{REPO}/votesForWeb/rc{leg}.csv.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "MexLegislativePipeline/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    out: dict[str, Path] = {}
    DL_DIR.mkdir(parents=True, exist_ok=True)
    for member in z.namelist():
        base = Path(member).name
        if not base.endswith(".csv"):
            continue
        target = DL_DIR / base
        target.write_bytes(z.read(member))
        for kind in ("dipdat", "votdat", "rc"):
            if base.startswith(f"{kind}{leg}"):
                out[kind] = target
    return out


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    roster_parts, event_parts, rc_parts = [], [], []
    for leg in ROLLCALL_LEGS:
        b = _fetch_rollcall_bundle(leg)
        rd = lambda p: f"read_csv_auto('{p.as_posix()}', header=true, all_varchar=true, sample_size=-1)"

        roster_parts.append(f"SELECT {leg} AS legislature, * FROM {rd(b['dipdat'])}")
        # vote events get a positional vote_seq matching the rc matrix row order
        event_parts.append(
            f"SELECT {leg} AS legislature, row_number() OVER () AS vote_seq, * FROM {rd(b['votdat'])}"
        )
        # unpivot the matrix: rows=votes (vote_seq), columns=legislator id, cell=code
        rc_parts.append(f"""
            SELECT {leg} AS legislature, vote_seq, legislator_id, vote_code
            FROM (
                UNPIVOT (SELECT row_number() OVER () AS vote_seq, * FROM {rd(b['rc'])})
                ON COLUMNS(* EXCLUDE (vote_seq))
                INTO NAME legislator_id VALUE vote_code
            )
            WHERE vote_code IS NOT NULL
        """)

    con.execute("CREATE TABLE raw.raw_dipmex_roster AS " + " UNION ALL BY NAME ".join(roster_parts))
    con.execute("CREATE TABLE raw.raw_dipmex_vote_events AS " + " UNION ALL BY NAME ".join(event_parts))
    con.execute("CREATE TABLE raw.raw_dipmex_rollcall AS " + " UNION ALL ".join(rc_parts))

    # recent rosters (real, roster-only) — schemas vary by legislature -> union by name
    recent = []
    for leg in RECENT_ROSTER_LEGS:
        p = _download(f"{REPO}/diputados/dip{leg}.csv", DL_DIR / f"dip{leg}.csv")
        recent.append(f"SELECT {leg} AS legislature, * FROM read_csv_auto('{p.as_posix()}', header=true, all_varchar=true, sample_size=-1)")
    con.execute("CREATE TABLE raw.raw_dipmex_roster_recent AS " + " UNION ALL BY NAME ".join(recent))

    for t in ("raw_dipmex_roster", "raw_dipmex_vote_events", "raw_dipmex_rollcall", "raw_dipmex_roster_recent"):
        n = con.sql(f"SELECT count(*) FROM raw.{t}").fetchone()[0]
        print(f"  raw.{t:<28} {n:>8,} rows")
    print("\n[+] Real dipMex landed in", DB_PATH)
    con.close()


if __name__ == "__main__":
    main()
