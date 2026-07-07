-- Every vote must resolve to a dimension version. A NULL legislator_key means
-- either the name never bridged to an id, or the as-of join found no covering
-- span. Both are failures we want to see, not silently tolerate.
SELECT
    vote_key,
    legislator_id,
    legislature,
    vote_event_id
FROM {{ ref('fact_vote') }}
WHERE legislator_key IS NULL
