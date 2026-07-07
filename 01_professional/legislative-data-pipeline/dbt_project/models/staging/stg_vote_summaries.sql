/*
 * stg_vote_summaries: one row per vote EVENT (the roll-call header).
 *
 * Source: raw.raw_dipmex_vote_events (dipMex votdat{60,61}.csv)
 * Grain: One row per vote event. `vote_seq` is the positional index that joins
 * back to the roll-call matrix (raw_dipmex_rollcall) row-for-row.
 *
 * Transformations: assemble the date from yr/mo/dy, build a stable vote_id,
 * carry the tallies, compute approval_rate.
 */

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_dipmex_vote_events') }}
)

SELECT
    MD5(CAST(legislature AS VARCHAR) || '|' || CAST(vote_seq AS VARCHAR)) AS vote_summary_sk,
    legislature,
    vote_seq,
    CAST(legislature AS VARCHAR) || '-' || LPAD(CAST(vote_seq AS VARCHAR), 4, '0') AS vote_id,
    {{ dipmex_date('yr', 'mo', 'dy') }} AS session_date,
    TRIM(title) AS description,
    COALESCE(TRY_CAST(favor AS INT), 0)  AS votes_for,
    COALESCE(TRY_CAST(contra AS INT), 0) AS votes_against,
    COALESCE(TRY_CAST(absten AS INT), 0) AS abstentions,
    COALESCE(TRY_CAST(ausen AS INT), 0)  AS absences,
    COALESCE(TRY_CAST(favor AS INT), 0) + COALESCE(TRY_CAST(contra AS INT), 0)
        + COALESCE(TRY_CAST(absten AS INT), 0) AS total_votes,
    CASE
        WHEN COALESCE(TRY_CAST(favor AS INT), 0) + COALESCE(TRY_CAST(contra AS INT), 0)
             + COALESCE(TRY_CAST(absten AS INT), 0) > 0
        THEN CAST(COALESCE(TRY_CAST(favor AS INT), 0) AS DOUBLE)
             / (COALESCE(TRY_CAST(favor AS INT), 0) + COALESCE(TRY_CAST(contra AS INT), 0)
                + COALESCE(TRY_CAST(absten AS INT), 0))
        ELSE NULL
    END AS approval_rate,
    TRIM(filename) AS detail_url
FROM source
