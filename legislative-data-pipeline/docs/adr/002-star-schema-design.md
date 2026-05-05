# ADR 002: Star Schema over Snowflake Schema for Dimensional Model

**Status:** Accepted
**Date:** 2026-03-24
**Context:** Designing the dimensional model for the legislative warehouse.

## Options considered

### Star schema
- Fully denormalized dimensions.
- Simple queries with direct fact → dimension joins.
- Some redundancy in dimension data (e.g., `party_name` repeated in every
  `dim_legislator` row).

### Snowflake schema
- Normalized dimensions (e.g., `dim_party` separated from `dim_legislator`,
  `dim_state` separated, etc.).
- Lower storage redundancy.
- More complex queries with multiple joins between dimensions.

### Wide denormalized table (one big table)
- Everything in a single flat table.
- Maximum query simplicity.
- Impossible to maintain history (SCD) without massive duplication.

## Decision

**Star schema** with SCD Type 2 on `dim_legislator`.

## Justification

1. **Low cardinality:** Mexico has ~500 deputies and ~128 senators per
   legislature, and ~8 relevant parties. Star-schema redundancy is
   negligible (~KB).

2. **Query simplicity:** Consumers (PowerBI, Streamlit) generate simple
   queries. A single `fact_vote → dim_legislator → dim_date` join covers
   90% of analyses.

3. **SCD requirement:** Caucus switches (party changes) are politically
   significant. A legislator who switches from PRI to MORENA mid-term
   must have two records in `dim_legislator` with date ranges. Star
   schema + SCD2 handles this cleanly.

4. **Tool compatibility:** PowerBI and dbt work naturally with star schemas.
   Relationships in PowerBI's model view map 1:1 to fact-dimension joins.

## Consequences

- `dim_party` exists as a separate table (not snowflake normalization but a
  reference with seed data).
- `dim_legislator` includes SCD2 fields: `effective_from`, `effective_to`,
  `is_current`, `_hash`.
- `fact_vote` uses `legislator_key` (surrogate) for the join, ensuring each
  vote is attributed to the correct party at that moment in time.
