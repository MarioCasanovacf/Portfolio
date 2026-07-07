/*
 * stg_sitl_votes: cleaned SITL per-deputy roll-call votes (recent legislatures).
 *
 * Grain: one row per deputy per vote event (a real cast vote, incl. ABSENT).
 * Source: raw.raw_sitl_votes joined to raw.raw_sitl_vote_meta for the real vote
 * DATE (the per-deputy pages carry no date; the estadistico summary does).
 *
 * Unlike dipMex, SITL votes carry the deputy NAME and the party label on EVERY
 * vote — so this source can drive a genuinely DATED party-switch history in
 * dim_legislator (a deputy's caucus can change between votes, with a real date).
 * legislator_id = SITL's `iddipt`, the stable per-deputy id within a legislature.
 *
 * Our per-deputy vote_cast has already been cross-validated to reproduce SITL's
 * official per-party tallies exactly on all 274 LXVI votes (see the singular test
 * assert_sitl_votes_match_official_tallies).
 */

WITH votes AS (
    SELECT
        CAST(legislature AS INT) AS legislature,
        CAST(votaciont AS INT)   AS vote_id,
        TRIM(iddipt)             AS legislator_id,
        TRIM(legislator_name)    AS full_name,
        TRIM(party)              AS party,
        vote_cast
    FROM {{ source('raw', 'raw_sitl_votes') }}
    WHERE vote_cast IS NOT NULL AND vote_cast <> ''
),

meta AS (
    SELECT
        CAST(legislature AS INT) AS legislature,
        CAST(votaciont AS INT)   AS vote_id,
        CAST(vote_date AS DATE)  AS vote_date
    FROM {{ source('raw', 'raw_sitl_vote_meta') }}
)

SELECT
    MD5(CAST(v.legislature AS VARCHAR) || '|' || CAST(v.vote_id AS VARCHAR) || '|' || v.legislator_id) AS vote_sk,
    v.legislature,
    v.vote_id,
    v.legislator_id,
    m.vote_date,
    v.full_name,
    v.party,
    v.vote_cast
FROM votes v
JOIN meta m USING (legislature, vote_id)
