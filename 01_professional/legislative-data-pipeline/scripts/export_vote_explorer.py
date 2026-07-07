"""Export the LXVI roll-call data as one compact JSON for the web vote explorer.

Reads the built DuckDB warehouse and emits a single static file the React island
fetches once. The per-deputy ballots are encoded as fixed-length strings indexed
by the master deputy list, so 274 votes x ~554 deputies costs ~150 KB, not megabytes.

    F = for      C = against    B = abstain    X = absent    - = not in record

Per-party tallies come from SITL's own official totals (raw_sitl_tallies) — the
same numbers a dbt test reconciles our scraped per-deputy votes against on all 274
votes. No network; pure read of data/legislative.duckdb.

Usage:  python scripts/export_vote_explorer.py [output.json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "data" / "legislative.duckdb"
DEFAULT_OUT = (
    REPO.parents[2] / "site" / "public" / "data" / "legislative-votes.json"
)

# Deputy-level long names -> the short labels SITL uses in its official tallies.
PARTY_SHORT = {
    "Movimiento Regeneración Nacional": "MORENA",
    "Partido Acción Nacional": "PAN",
    "Partido Verde Ecologista de México": "PVEM",
    "Partido del Trabajo": "PT",
    "Partido Revolucionario Institucional": "PRI",
    "Movimiento Ciudadano": "MC",
    "Independiente": "IND",
}

# Display order: governing coalition, then opposition, then the rest.
PARTY_ORDER = ["MORENA", "PVEM", "PT", "PRI", "PAN", "MC", "IND", "PRD"]
PARTY_BLOC = {
    "MORENA": "government", "PVEM": "government", "PT": "government",
    "PRI": "opposition", "PAN": "opposition", "MC": "opposition",
    "IND": "other", "PRD": "other",
}
PARTY_FULL = {
    "MORENA": "Movimiento Regeneración Nacional",
    "PVEM": "Partido Verde Ecologista de México",
    "PT": "Partido del Trabajo",
    "PRI": "Partido Revolucionario Institucional",
    "PAN": "Partido Acción Nacional",
    "MC": "Movimiento Ciudadano",
    "IND": "Independiente",
    "PRD": "Partido de la Revolución Democrática",
}

SENSE = {"FOR": "F", "AGAINST": "C", "ABSTAIN": "B", "ABSENT": "X", "PRESENT": "P"}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    con = duckdb.connect(str(DB), read_only=True)

    # --- master deputy list: one row per seat occupant, modal (most-held) party ---
    deputy_rows = con.execute(
        """
        WITH modal AS (
            SELECT legislator_id, party,
                   ROW_NUMBER() OVER (PARTITION BY legislator_id
                                      ORDER BY COUNT(*) DESC, party) AS rn
            FROM main.stg_sitl_votes
            GROUP BY legislator_id, party
        )
        SELECT v.legislator_id,
               MIN(v.full_name)              AS full_name,
               ANY_VALUE(m.party)            AS party_long
        FROM main.stg_sitl_votes v
        JOIN modal m ON m.legislator_id = v.legislator_id AND m.rn = 1
        GROUP BY v.legislator_id
        ORDER BY MIN(v.full_name)
        """
    ).fetchall()

    deputies = []
    idx_of: dict[str, int] = {}
    for i, (lid, name, party_long) in enumerate(deputy_rows):
        idx_of[lid] = i
        deputies.append(
            {"id": lid, "name": name, "party": PARTY_SHORT.get(party_long, party_long)}
        )
    n_dep = len(deputies)

    # --- proposals: title + date + official per-party tallies ---
    meta = {
        str(r[0]): {"date": r[1], "title": r[2]}
        for r in con.execute(
            "SELECT CAST(votaciont AS INT), vote_date, title FROM raw.raw_sitl_vote_meta"
        ).fetchall()
    }

    tallies: dict[str, dict[str, dict]] = {}
    for vid, party, f, c, b, asis, x in con.execute(
        """
        SELECT CAST(votaciont AS INT), party,
               CAST(a_favor AS INT), CAST(en_contra AS INT), CAST(abstencion AS INT),
               CAST(solo_asistencia AS INT), CAST(ausente AS INT)
        FROM raw.raw_sitl_tallies
        """
    ).fetchall():
        tallies.setdefault(str(vid), {})[party] = {
            "for": f, "against": c, "abstain": b, "present": asis, "absent": x
        }

    vote_ids = sorted(
        (r[0] for r in con.execute(
            "SELECT DISTINCT CAST(vote_event_id AS INT) FROM main.fact_vote WHERE legislature = 66"
        ).fetchall())
    )

    # --- ballots: per vote, sense per deputy, encoded as a fixed-length string ---
    cast_rows = con.execute(
        """
        SELECT CAST(vote_event_id AS INT), legislator_id, vote_cast
        FROM main.fact_vote WHERE legislature = 66
        """
    ).fetchall()
    by_vote: dict[int, dict[str, str]] = {}
    for vid, lid, cast in cast_rows:
        by_vote.setdefault(vid, {})[lid] = SENSE.get(cast, "-")

    proposals = []
    ballots: dict[str, str] = {}
    for vid in vote_ids:
        key = str(vid)
        m = meta.get(key, {"date": None, "title": f"Vote {vid}"})
        party_tallies = tallies.get(key, {})
        totals = {"for": 0, "against": 0, "abstain": 0, "present": 0, "absent": 0}
        for t in party_tallies.values():
            for k in totals:
                totals[k] += t[k]
        proposals.append({
            "id": key,
            "n": vid,
            "date": m["date"],
            "title": m["title"],
            "totals": totals,
            "byParty": party_tallies,
        })
        senses = by_vote.get(vid, {})
        ballots[key] = "".join(senses.get(d["id"], "-") for d in deputies)

    parties = [
        {"code": p, "full": PARTY_FULL.get(p, p), "bloc": PARTY_BLOC.get(p, "other")}
        for p in PARTY_ORDER
        if any(p in t for t in tallies.values())
    ]

    payload = {
        "legislature": 66,
        "chamber": "Chamber of Deputies",
        "source": "SITL (sitl.diputados.gob.mx), reconciled to official per-vote tallies",
        "senseLegend": {"F": "For", "C": "Against", "B": "Abstain", "X": "Absent", "P": "Present"},
        "parties": parties,
        "deputies": deputies,
        "proposals": proposals,
        "ballots": ballots,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({size_kb:.0f} KB)")
    print(f"  {len(deputies)} deputies · {len(proposals)} proposals · "
          f"{len(parties)} parties · {sum(len(b) for b in ballots.values()):,} ballot cells")


if __name__ == "__main__":
    main()
