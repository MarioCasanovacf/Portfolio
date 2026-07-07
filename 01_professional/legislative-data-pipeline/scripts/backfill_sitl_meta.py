"""Backfill SITL per-vote metadata + official tallies from already-saved
`estadistico` pages — NO network.

Re-derives `sitl_vote_meta_{slug}.csv` and `sitl_tallies_{slug}.csv` from the raw
HTML the scraper already persisted, using the exact same parser the live scraper
uses (`SitlScraper._parse_estadistico`). Idempotent: rewrites the two CSVs each
run. Needed only to enrich data captured before metadata capture was added; new
runs of the scraper produce these files natively.

Usage:  PYTHONPATH=src python scripts/backfill_sitl_meta.py [legislature=66]
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capture.sitl import LEGISLATURES, META_FIELDS, TALLY_FIELDS, SitlScraper


def votaciont_to_pert(raw_dir: Path) -> dict[int, int]:
    """Map each votaciont to the period (pert) whose vote-list page contains it."""
    mapping: dict[int, int] = {}
    for f in sorted(raw_dir.glob("votelist_pert*.html")):
        pert = int(re.search(r"votelist_pert(\d+)", f.name).group(1))
        for m in re.finditer(r"votaciont=(\d+)", f.read_text(errors="replace")):
            mapping.setdefault(int(m.group(1)), pert)
    return mapping


def main(legislature: int = 66) -> None:
    slug = LEGISLATURES[legislature]
    base = Path(__file__).resolve().parents[1] / "data" / "raw" / "sitl" / slug
    raw = base / "raw"
    pert_of = votaciont_to_pert(raw)

    meta_rows: list[dict] = []
    tally_rows: list[dict] = []
    ests = sorted(raw.glob("estadistico_v*.html"),
                  key=lambda p: int(re.search(r"_v(\d+)", p.name).group(1)))
    for f in ests:
        vot = int(re.search(r"_v(\d+)", f.name).group(1))
        parsed = SitlScraper._parse_estadistico(
            f.read_text(errors="replace"), legislature, vot, pert_of.get(vot, 0)
        )
        meta_rows.append(parsed)
        tally_rows.extend(parsed["tallies"])

    meta_csv = base / f"sitl_vote_meta_{slug}.csv"
    tallies_csv = base / f"sitl_tallies_{slug}.csv"
    for path, fields, rows in [
        (meta_csv, META_FIELDS, meta_rows),
        (tallies_csv, TALLY_FIELDS, tally_rows),
    ]:
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    missing = [m["votaciont"] for m in meta_rows if not m["vote_date"]]
    print(f"meta rows : {len(meta_rows):>5}  -> {meta_csv.name}")
    print(f"tally rows: {len(tally_rows):>5}  -> {tallies_csv.name}")
    print(f"votes with UNPARSED date: {len(missing)} {missing[:10]}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 66)
