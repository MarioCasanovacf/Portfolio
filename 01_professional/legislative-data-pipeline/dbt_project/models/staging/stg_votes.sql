/*
 * stg_votes: cleaned individual vote records (one row per legislator per vote).
 *
 * Source: raw.raw_dipmex_rollcall (the unpivoted roll-call matrix) joined to
 * raw vote events for the date. The matrix is keyed by the stable legislator
 * `id`, so votes carry legislator_id NATIVELY — no name bridge is needed for
 * dipMex (the fuzzy bridge is reserved for the name-only SITL/recent path).
 *
 * Vote codes: 1=favor, 2=contra, 3=abstención, 5=ausente. Code 0 ("not in the
 * seat" for that vote — e.g. a suplente while the propietario serves) and the
 * rare code 4 (quorum marker) are excluded, so every row is a real cast vote.
 */

WITH rollcall AS (
    SELECT * FROM {{ source('raw', 'raw_dipmex_rollcall') }}
),

events AS (
    SELECT legislature, vote_seq, vote_id, session_date
    FROM {{ ref('stg_vote_summaries') }}
)

SELECT
    MD5(CAST(rc.legislature AS VARCHAR) || '|' || CAST(rc.vote_seq AS VARCHAR) || '|' || rc.legislator_id) AS vote_sk,
    rc.legislature,
    e.vote_id,
    rc.vote_seq,
    TRIM(rc.legislator_id) AS legislator_id,
    e.session_date AS vote_date,
    CASE rc.vote_code
        WHEN '1' THEN 'FOR'
        WHEN '2' THEN 'AGAINST'
        WHEN '3' THEN 'ABSTAIN'
        WHEN '5' THEN 'ABSENT'
    END AS vote_cast
FROM rollcall rc
JOIN events e
    ON rc.legislature = e.legislature
    AND rc.vote_seq = e.vote_seq
WHERE rc.vote_code IN ('1', '2', '3', '5')
