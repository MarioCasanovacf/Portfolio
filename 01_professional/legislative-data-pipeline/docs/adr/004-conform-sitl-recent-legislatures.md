# ADR 004: Conform the SITL recent legislatures into one star (dated party-run history)

**Status:** Accepted
**Date:** 2026-06-13
**Context:** ADR 003 grounded the star on the dipMex academic dataset, which has a
*complete* roll-call record only for legislatures **60-61** and forces a
**term-grain** history (its roster in/out dates are too imprecise to bound votes).
The priority, though, is the **recent** legislatures — modern legislative history.
dipMex carries no individual roll-calls there, so the votes come from the Cámara
de Diputados **SITL** site (`sitl.diputados.gob.mx`), scraped per deputy. Unlike
dipMex, SITL carries the deputy **name and party label on every vote** and a real
**vote date** — which is exactly what a *dated* caucus-switch history needs.

The decision was how to integrate it: a separate "recent" star, or one conformed
star spanning all legislatures.

## Decision

**Conform SITL into the SAME star** — one `dim_legislator`, one `fact_vote`
spanning legislatures 60, 61 (dipMex) and 66 (SITL) — rather than a parallel
`fact_vote_recent`. "A legislator cast a vote on a roll-call on a date" is a
single business process; one conformed dimension + one fact is the dimensionally
correct model, and splitting the same grain into two facts is an anti-pattern that
forces consumers to UNION what is conceptually one table. The historization
mechanism varies *inside* the dimension by what each source can support.

1. **Capture & load.** `src/capture/sitl.py` captures per-deputy votes, per-vote
   metadata (date + title), and SITL's official per-party tallies; `scripts/ingest_sitl.py`
   lands them into `raw.raw_sitl_{votes,vote_meta,tallies}` (additive, no network —
   run after `ingest_dipmex.py`, which rebuilds the DB).
2. **Staging.** `stg_sitl_votes` joins the per-deputy votes to the per-vote
   metadata for the real `vote_date`.
3. **Dated party-run versioning.** In `dim_legislator`, the SITL branch versions a
   deputy by **dated party run**: a gaps-and-islands over the party label ordered
   by `vote_date` opens a new version each time the caucus changes. `effective_from`
   = the first vote date of the run; `effective_to` = the next run's start (or term
   end + 1). This is the genuine dated caucus history the term-grain dipMex source
   cannot express.
4. **Conformed key & join.** Surrogate key `md5(source | legislator_id | legislature
   | effective_from)` and the as-of join key `(source, legislator_id)` keep the two
   id-spaces (dipMex **seat** ids vs SITL **iddipt**) from ever colliding.
5. **Cross-validation test.** `assert_sitl_votes_match_official_tallies` aggregates
   our per-deputy `vote_cast` per vote and asserts it equals SITL's official
   tallies — green on **all 274 LXVI votes** (our independent capture reproduces
   the official record exactly).

### Honest reading of the "party switches"

The dimension faithfully records every party-label run, but a raw "≥2 versions"
count overstates real defections, so `v_legislator_party_switches` classifies them:

- **no_change** (472 deputies) — one party run.
- **oscillation** (67) — a party recurs (runs > distinct parties): almost always
  intra-coalition **label noise** (MORENA / PVEM / PT are the governing "Juntos
  Hacemos Historia" coalition and SITL labels some coaligados inconsistently per
  vote), *not* a real switch.
- **monotonic_switch** (15) — a clean directional move, the genuine-defection
  candidate — and even most of these are intra-coalition reassignments; only one
  (PAN → MC) is a cross-bloc move.

So the headline "82 switches" honestly deflates to ~15 clean moves. Cohesion is
near-total across every caucus (Rice index 0.993-1.00 in LXVI), so this is a
highly disciplined chamber, not a volatile one.

### What is deliberately NOT done

Cross-era **person** identity (linking a 60-61 deputy to the same human in 66) is
not modeled: the id-spaces differ and it needs the fuzzy name bridge (`normalize_name`
macro + overrides seed, reserved for this). The conformed dimension is at the
(source, legislator, validity-span) grain; person-across-eras is an optional later
enrichment, not required for any analysis here.

## Consequences

- One conformed star: `fact_vote` holds **798,445 real attributed votes** (dipMex
  60 = 296,200, 61 = 365,298; SITL 66 = 136,947) with **zero NULL legislator keys**;
  `dbt build` is fully green (incl. the official-tally cross-check).
- The recent-legislature analysis the project is really about now exists: dated
  caucus history, party cohesion, and attendance for LXVI — see the `v_*` views.
- Capture lesson baked into the scraper: SITL's `partidot` is a per-vote **page
  index**, not a stable party id; the party is read from each page and the deputy
  pages are followed via the `estadistico` summary (see `src/capture/sitl.py`).
