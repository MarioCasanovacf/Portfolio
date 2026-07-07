/*
 * v_legislator_party_switches: per recent-legislature (SITL) deputy, their dated
 * caucus history summarized and classified HONESTLY.
 *
 * The dated dimension faithfully records every party-label run; this view keeps
 * that fidelity but adds the interpretation, because a raw "≥2 versions" count
 * overstates real defections:
 *
 *   no_change        - a single party run (the label never changed)
 *   monotonic_switch - n runs over n DISTINCT parties (no party recurs): a clean,
 *                      directional move — the genuine-defection candidate
 *   oscillation      - a party recurs (runs > distinct parties): almost always
 *                      intra-coalition LABEL noise (MORENA / PVEM / PT are the
 *                      governing "Juntos Hacemos Historia" coalition and SITL
 *                      labels some coaligados inconsistently), NOT a real switch
 *
 * Even most monotonic switches are intra-coalition reassignments, so a true
 * cross-bloc defection = monotonic_switch AND first/last parties on opposite
 * sides. The verdict is left to the consumer; this view exposes the raw shape.
 */

{{ config(materialized='view') }}

WITH versions AS (
    SELECT
        legislator_id,
        MAX(full_name)                       AS full_name,
        COUNT(*)                             AS n_versions,
        COUNT(DISTINCT party)                AS n_parties,
        MIN(effective_from)                  AS first_seen,
        FIRST(party ORDER BY effective_from) AS first_party,
        LAST(party  ORDER BY effective_from) AS last_party
    FROM {{ ref('dim_legislator') }}
    WHERE source = 'sitl'
    GROUP BY legislator_id
)

SELECT
    legislator_id,
    full_name,
    n_versions,
    n_parties,
    first_party,
    last_party,
    CASE
        WHEN n_versions = 1         THEN 'no_change'
        WHEN n_versions = n_parties THEN 'monotonic_switch'
        ELSE 'oscillation'
    END AS switch_kind
FROM versions
