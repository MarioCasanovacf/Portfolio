/*
 * dim_legislator: dated version history of legislators (a functional SCD Type 2),
 * CONFORMED across both real sources — one dimension, one grain ("a legislator's
 * standing valid over a date range"), the historization mechanism varying by what
 * each source can support:
 *
 *  - dipMex (legs 60-61): one version per (legislator, LEGISLATURE TERM). The
 *    roster in/out dates proved too imprecise to bound the roll-call (~4% of votes
 *    fall outside), so we version by the reliable term and keep occupancy (entry /
 *    licencia) as descriptive ATTRIBUTES. Membership = roster ∪ everyone who
 *    actually cast a vote, so no real vote is orphaned.
 *
 *  - SITL (legs 64-66): one version per DATED PARTY RUN. SITL carries the party
 *    label on EVERY vote, so caucus changes are real and dated — a new version
 *    starts each time a deputy's party label changes between votes (a
 *    gaps-and-islands over party ordered by vote_date). This is the genuine dated
 *    caucus-switch history the term-grain dipMex source cannot support.
 *
 * Conformed surrogate key md5(source | legislator_id | legislature | effective_from)
 * uses business dates only, so it never churns across runs and fact_vote's FK
 * stays valid. is_current marks each legislator's latest version.
 */

{{ config(
    materialized='incremental',
    unique_key='legislator_key',
    incremental_strategy='delete+insert'
) }}

WITH calendar AS (
    SELECT legislature, start_date, end_date FROM {{ ref('legislature_calendar') }}
),

-- ===================== dipMex: one version per term =======================
deputies AS (
    SELECT * FROM {{ ref('stg_deputies') }}
),
members AS (
    SELECT legislator_id, legislature FROM deputies
    UNION
    SELECT DISTINCT legislator_id, legislature FROM {{ ref('stg_votes') }}
),
dipmex_versions AS (
    SELECT
        'dipmex'                                            AS source,
        m.legislator_id,
        m.legislature,
        d.full_name,
        d.party,
        d.state,
        COALESCE(d.is_suplente, m.legislator_id LIKE '%s')  AS is_suplente,
        d.in1_date                                          AS entered_date,
        d.out1_date                                         AS licencia_start_date,
        d.in2_date                                          AS licencia_return_date,
        c.start_date                                        AS effective_from,
        c.end_date + 1                                      AS effective_to
    FROM members m
    LEFT JOIN deputies d
        ON m.legislator_id = d.legislator_id AND m.legislature = d.legislature
    JOIN calendar c ON c.legislature = m.legislature
),

-- ===================== SITL: one version per dated party run ==============
sitl_daily AS (
    -- collapse a deputy's votes to one party per day (party is constant within a
    -- deputy-day; this denoises before the run detection)
    SELECT legislator_id, legislature, vote_date,
           MIN(party)     AS party,
           MAX(full_name) AS full_name
    FROM {{ ref('stg_sitl_votes') }}
    GROUP BY legislator_id, legislature, vote_date
),
sitl_flagged AS (
    SELECT *,
        CASE WHEN party IS DISTINCT FROM
             LAG(party) OVER (PARTITION BY legislator_id ORDER BY vote_date)
             THEN 1 ELSE 0 END AS is_change
    FROM sitl_daily
),
sitl_islands AS (
    SELECT *,
        SUM(is_change) OVER (PARTITION BY legislator_id ORDER BY vote_date) AS island
    FROM sitl_flagged
),
sitl_runs AS (
    SELECT
        legislator_id,
        MAX(legislature) AS legislature,
        MAX(full_name)   AS full_name,
        MIN(party)       AS party,           -- constant within an island
        island,
        MIN(vote_date)   AS effective_from
    FROM sitl_islands
    GROUP BY legislator_id, island
),
sitl_versions AS (
    SELECT
        'sitl'                                              AS source,
        r.legislator_id,
        r.legislature,
        r.full_name,
        r.party,
        CAST(NULL AS VARCHAR)                               AS state,
        CAST(NULL AS BOOLEAN)                               AS is_suplente,
        CAST(NULL AS DATE)                                  AS entered_date,
        CAST(NULL AS DATE)                                  AS licencia_start_date,
        CAST(NULL AS DATE)                                  AS licencia_return_date,
        r.effective_from,
        COALESCE(
            LEAD(r.effective_from) OVER (PARTITION BY r.legislator_id ORDER BY r.effective_from),
            c.end_date + 1
        )                                                   AS effective_to
    FROM sitl_runs r
    JOIN calendar c ON c.legislature = r.legislature
),

-- ===================== conform + surrogate key ===========================
unioned AS (
    SELECT * FROM dipmex_versions
    UNION ALL BY NAME
    SELECT * FROM sitl_versions
)

SELECT
    {{ generate_surrogate_key(['source', 'legislator_id', 'legislature', 'effective_from']) }} AS legislator_key,
    source,
    legislator_id,
    full_name,
    party,
    state,
    is_suplente,
    entered_date,
    licencia_start_date,
    licencia_return_date,
    legislature,
    effective_from,
    effective_to,
    (effective_to = MAX(effective_to) OVER (PARTITION BY source, legislator_id)) AS is_current,
    {{ generate_surrogate_key(['party', 'state']) }} AS _hash
FROM unioned
