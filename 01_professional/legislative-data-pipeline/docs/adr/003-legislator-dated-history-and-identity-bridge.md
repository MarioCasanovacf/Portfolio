# ADR 003: Dated version history on `dim_legislator` (a functional SCD2), grounded on real dipMex data

**Status:** Accepted
**Date:** 2026-06-09
**Context:** The first cut of `dim_legislator` had *scaffolding* for a dated version history (a `_hash`
column, `effective_from`/`effective_to`/`is_current`) but no working
historization: every row was stamped `is_current = TRUE` with a single hard-coded
`effective_from`, and `fact_vote` joined the dimension by **free-text name**
filtered on `is_current = TRUE`. Worse, the configured dipMex capture pointed at
files that **do not exist** (`data/votaciones##.csv` → 404), so the pipeline had
never run against real data at all — a synthetic fixture had been masking it.

## Decision

Re-ground the whole star on the **real dipMex academic dataset**
(`github.com/emagar/dipMex`, a static, citable source — the sustainable backbone,
no fragile live scraping) and build a functional dated version history (SCD Type 2) + as-of fact on it.

1. **Real ingestion** (`scripts/ingest_dipmex.py`). dipMex provides a *complete*
   roll-call record for legislatures **60 and 61**: `dipdat{leg}.csv` (roster with
   real seat entry/exit dates), `votdat{leg}.csv` (vote events with dates/tallies),
   and `rc{leg}.csv` (the roll-call MATRIX — rows = votes, columns = the stable
   legislator `id`). The matrix is unpivoted to one row per legislator-vote
   (~1.33M real records). Recent rosters (dip64-66) are landed too.
2. **id-native votes.** The matrix columns ARE the stable ids, so votes carry
   `legislator_id` directly — **no name bridge is needed for dipMex**. The fuzzy
   name-bridge (`normalize_name` macro, overrides seed) is retained for the
   name-only **SITL** path (recent legislatures), where it is genuinely required.
3. **As-of join.** `fact_vote` joins `dim_legislator` on `legislator_id` and
   `vote_date ∈ [effective_from, effective_to)` (half-open), not on `is_current`.
4. **Version by LEGISLATURE TERM**, with stable key `md5(legislator_id |
   legislature)`. A seat held across terms gets one version per term, so each vote
   is attributed to the term's occupant and party. `is_current` marks the latest
   term.
5. **Tests:** zero NULL `legislator_key` in the fact; no overlapping spans; one
   `is_current` per legislator; FK relationship fact→dim. All green on real data.

### Key sub-decision: version by term, not by the roster's in/out dates

The intent was to version by the roster's seat entry/exit dates (propietario /
suplente / licencias). On the real data that **fails**: the in/out dates are too
imprecise to *bound* the voting record — ~4% of real votes fall outside the
recorded occupancy window (legislators vote after a recorded exit, or appear in
the roll-call with no roster entry at all). The roll-call matrix is the
authoritative presence record, so we version by the reliable **term boundary**,
keep occupancy (entry / licencia dates) as descriptive **attributes**, and drive
membership from the **union of the roster and everyone who actually voted** — so
no real vote is orphaned. Note the dipMex `id` is a **seat** id
(state+district+propietario/suplente), stable within a legislature and reused
across terms by different people; term-versioning handles that correctly.

Dated **intra-term party-switch** versioning (the original ambition) belongs to
the **recent legislatures (64-66)**, fed by the dip64-66 in/out dates + the SITL
per-deputy roll-call scrape — where caucus switches are real, dated, and the
name-bridge earns its place. That build is **ADR 004** (the SITL recent
legislatures, conformed into this same star with a dated party-run history).

### Why a custom incremental model, not a dbt snapshot

`dbt snapshot` stamps `dbt_valid_from` = the ETL run timestamp; we need **business
dates** (term start/end). Hence a hand-rolled incremental model and no
`snapshots/` directory.

## Consequences

- The star is genuinely **real and reproducible**: `python scripts/ingest_dipmex.py`
  then `dbt build` → 661,498 real attributed votes across legs 60-61, all tests
  green. A real analysis falls straight out (e.g. party cohesion / Rice index:
  PVEM 98.8%, PRI 98.5%, PAN 98.1%, … PT 89.3% in LXI).
- Surrogate keys are stable across runs (no `ROW_NUMBER()` churn), so the fact FK
  holds.
- Honest coverage boundary: dipMex provides complete roll-calls only for legs
  60-61 (rc62 is RData-only; 64-66 individual votes are not in dipMex). Recent
  legislatures are the SITL extension.
- New/changed: `scripts/ingest_dipmex.py`, `macros/{dipmex_date,normalize_name}`,
  `seeds/legislature_calendar.csv`, rewritten staging (`stg_deputies`,
  `stg_votes`, `stg_vote_summaries`), `dim_legislator`, `fact_vote`, and tests.
