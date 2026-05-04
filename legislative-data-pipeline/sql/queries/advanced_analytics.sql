/*
 * ADVANCED SQL SHOWCASE — Mexican Legislative Analytics
 * ======================================================
 * Queries demonstrating advanced SQL techniques applied to legislative data.
 * Each query addresses a specific business question.
 *
 * Techniques demonstrated:
 *   - Window functions (LAG, LEAD, NTILE, DENSE_RANK, PERCENT_RANK)
 *   - Recursive CTEs
 *   - PIVOT/UNPIVOT
 *   - Running aggregates and moving averages
 *   - Sessionization
 *   - Gap-and-island detection
 */


-- =============================================================================
-- Q1: Party Loyalty Score with Percentile Ranking
-- Business question: Which legislators vote most/least with their party?
-- Technique: Window functions (PERCENT_RANK, NTILE)
-- =============================================================================

WITH party_majority AS (
    -- For each vote event, determine the majority position of each party.
    SELECT
        vote_event_id,
        legislature,
        party,
        CASE
            WHEN SUM(CASE WHEN vote_cast = 'FOR' THEN 1 ELSE 0 END) >=
                 SUM(CASE WHEN vote_cast = 'AGAINST' THEN 1 ELSE 0 END)
            THEN 'FOR'
            ELSE 'AGAINST'
        END AS party_position
    FROM analytics.fact_vote fv
    JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
    WHERE vote_cast IN ('FOR', 'AGAINST')
    GROUP BY vote_event_id, legislature, party
),

loyalty AS (
    -- Calculate how often each legislator votes with their party's majority.
    SELECT
        dl.legislator_key,
        dl.full_name,
        dl.party,
        dl.legislature,
        COUNT(*) AS total_votes,
        SUM(CASE WHEN fv.vote_cast = pm.party_position THEN 1 ELSE 0 END) AS aligned_votes,
        aligned_votes::FLOAT / NULLIF(total_votes, 0) AS loyalty_score
    FROM analytics.fact_vote fv
    JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
    JOIN party_majority pm
        ON fv.vote_event_id = pm.vote_event_id
        AND dl.party = pm.party
    WHERE fv.vote_cast IN ('FOR', 'AGAINST')
    GROUP BY dl.legislator_key, dl.full_name, dl.party, dl.legislature
)

SELECT
    full_name,
    party,
    legislature,
    total_votes,
    loyalty_score,
    PERCENT_RANK() OVER (PARTITION BY party ORDER BY loyalty_score) AS loyalty_percentile,
    NTILE(4) OVER (PARTITION BY party ORDER BY loyalty_score) AS loyalty_quartile,
    DENSE_RANK() OVER (PARTITION BY party ORDER BY loyalty_score DESC) AS rank_in_party
FROM loyalty
WHERE total_votes >= 10
ORDER BY party, loyalty_score DESC;


-- =============================================================================
-- Q2: Voting Streaks — Gap and Island Detection
-- Business question: What are the longest consecutive approval/rejection streaks?
-- Technique: Gap-and-island pattern with ROW_NUMBER difference
-- =============================================================================

WITH ordered_votes AS (
    SELECT
        vote_event_id,
        date_key,
        is_approved,
        ROW_NUMBER() OVER (ORDER BY date_key) AS rn,
        ROW_NUMBER() OVER (PARTITION BY is_approved ORDER BY date_key) AS grp_rn
    FROM analytics.fact_vote_summary
    WHERE date_key IS NOT NULL
),

islands AS (
    SELECT
        is_approved,
        MIN(date_key) AS streak_start,
        MAX(date_key) AS streak_end,
        COUNT(*) AS streak_length,
        rn - grp_rn AS island_id
    FROM ordered_votes
    GROUP BY is_approved, rn - grp_rn
)

SELECT
    CASE WHEN is_approved THEN 'Approval Streak' ELSE 'Rejection Streak' END AS streak_type,
    streak_start,
    streak_end,
    streak_length
FROM islands
WHERE streak_length >= 3
ORDER BY streak_length DESC
LIMIT 20;


-- =============================================================================
-- Q3: Rolling 30-Vote Approval Rate with Trend Detection
-- Business question: Is the legislature becoming more or less contentious?
-- Technique: Window frames (ROWS BETWEEN), LAG for trend
-- =============================================================================

WITH vote_timeline AS (
    SELECT
        vote_event_id,
        date_key,
        approval_rate,
        AVG(approval_rate) OVER (
            ORDER BY date_key
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS rolling_30_avg,
        LAG(approval_rate, 10) OVER (ORDER BY date_key) AS rate_10_votes_ago
    FROM analytics.fact_vote_summary
    WHERE date_key IS NOT NULL
        AND approval_rate IS NOT NULL
)

SELECT
    vote_event_id,
    date_key,
    ROUND(approval_rate, 3) AS approval_rate,
    ROUND(rolling_30_avg, 3) AS rolling_30_avg,
    ROUND(approval_rate - COALESCE(rate_10_votes_ago, approval_rate), 3) AS momentum,
    CASE
        WHEN rolling_30_avg > 0.8 THEN 'CONSENSUS'
        WHEN rolling_30_avg > 0.6 THEN 'NORMAL'
        WHEN rolling_30_avg > 0.4 THEN 'CONTENTIOUS'
        ELSE 'GRIDLOCK'
    END AS legislative_climate
FROM vote_timeline
ORDER BY date_key;


-- =============================================================================
-- Q4: Cross-Party Voting Alignment Matrix (PIVOT)
-- Business question: Which parties vote together most often?
-- Technique: Self-join + PIVOT to create alignment heatmap data
-- =============================================================================

WITH party_vote_position AS (
    SELECT
        fv.vote_event_id,
        dl.party,
        -- Party position = majority vote of party members
        CASE
            WHEN SUM(CASE WHEN fv.vote_cast = 'FOR' THEN 1 ELSE 0 END) >
                 SUM(CASE WHEN fv.vote_cast = 'AGAINST' THEN 1 ELSE 0 END)
            THEN 'FOR'
            ELSE 'AGAINST'
        END AS position
    FROM analytics.fact_vote fv
    JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
    WHERE fv.vote_cast IN ('FOR', 'AGAINST')
    GROUP BY fv.vote_event_id, dl.party
    HAVING COUNT(*) >= 3
),

alignment AS (
    SELECT
        a.party AS party_a,
        b.party AS party_b,
        COUNT(*) AS shared_votes,
        SUM(CASE WHEN a.position = b.position THEN 1 ELSE 0 END) AS aligned,
        aligned::FLOAT / NULLIF(shared_votes, 0) AS alignment_rate
    FROM party_vote_position a
    JOIN party_vote_position b
        ON a.vote_event_id = b.vote_event_id
        AND a.party < b.party  -- avoid self-join and duplicates
    GROUP BY a.party, b.party
)

SELECT
    party_a,
    party_b,
    shared_votes,
    ROUND(alignment_rate, 3) AS alignment_rate,
    CASE
        WHEN alignment_rate > 0.8 THEN 'COALITION'
        WHEN alignment_rate > 0.6 THEN 'FREQUENT_ALLIES'
        WHEN alignment_rate > 0.4 THEN 'SWING'
        ELSE 'OPPOSITION'
    END AS relationship
FROM alignment
WHERE shared_votes >= 10
ORDER BY alignment_rate DESC;


-- =============================================================================
-- Q5: Legislator Attendance Sessionization
-- Business question: Do legislators have patterns of consecutive absences?
-- Technique: Sessionization with LAG and conditional running sum
-- =============================================================================

WITH attendance_log AS (
    SELECT
        dl.legislator_key,
        dl.full_name,
        dl.party,
        fv.date_key,
        fv.is_present,
        LAG(fv.is_present) OVER (
            PARTITION BY dl.legislator_key ORDER BY fv.date_key
        ) AS prev_present
    FROM analytics.fact_vote fv
    JOIN analytics.dim_legislator dl ON fv.legislator_key = dl.legislator_key
),

session_boundaries AS (
    SELECT
        *,
        CASE
            WHEN is_present != COALESCE(prev_present, is_present) THEN 1
            ELSE 0
        END AS new_session,
        SUM(CASE WHEN is_present != COALESCE(prev_present, is_present) THEN 1 ELSE 0 END)
            OVER (PARTITION BY legislator_key ORDER BY date_key) AS session_id
    FROM attendance_log
),

absence_sessions AS (
    SELECT
        legislator_key,
        full_name,
        party,
        session_id,
        is_present,
        COUNT(*) AS session_length,
        MIN(date_key) AS session_start,
        MAX(date_key) AS session_end
    FROM session_boundaries
    GROUP BY legislator_key, full_name, party, session_id, is_present
)

SELECT
    full_name,
    party,
    session_length AS consecutive_absences,
    session_start,
    session_end
FROM absence_sessions
WHERE NOT is_present
    AND session_length >= 5
ORDER BY session_length DESC
LIMIT 50;


-- =============================================================================
-- Q6: Recursive CTE — Legislative Influence Chain
-- Business question: If legislator A always votes with B, and B with C,
--                    what are the influence chains?
-- Technique: Recursive CTE for graph traversal
-- =============================================================================

WITH vote_pairs AS (
    -- Find pairs of legislators who vote identically > 90% of the time
    SELECT
        a.legislator_key AS legislator_a,
        b.legislator_key AS legislator_b,
        COUNT(*) AS shared_votes,
        SUM(CASE WHEN a.vote_cast = b.vote_cast THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS alignment
    FROM analytics.fact_vote a
    JOIN analytics.fact_vote b
        ON a.vote_event_id = b.vote_event_id
        AND a.legislator_key < b.legislator_key
    WHERE a.vote_cast IN ('FOR', 'AGAINST')
        AND b.vote_cast IN ('FOR', 'AGAINST')
    GROUP BY a.legislator_key, b.legislator_key
    HAVING COUNT(*) >= 20
        AND alignment > 0.9
),

RECURSIVE influence_chain AS (
    -- Base case: direct high-alignment pairs
    SELECT
        legislator_a AS chain_start,
        legislator_b AS chain_end,
        1 AS depth,
        CAST(legislator_a AS VARCHAR) || ' → ' || CAST(legislator_b AS VARCHAR) AS path
    FROM vote_pairs

    UNION ALL

    -- Recursive case: extend chain through transitive alignment
    SELECT
        ic.chain_start,
        vp.legislator_b AS chain_end,
        ic.depth + 1,
        ic.path || ' → ' || CAST(vp.legislator_b AS VARCHAR)
    FROM influence_chain ic
    JOIN vote_pairs vp ON ic.chain_end = vp.legislator_a
    WHERE ic.depth < 4
        AND POSITION(CAST(vp.legislator_b AS VARCHAR) IN ic.path) = 0  -- prevent cycles
)

SELECT
    chain_start,
    chain_end,
    depth AS chain_length,
    path
FROM influence_chain
WHERE depth >= 2
ORDER BY depth DESC, chain_start
LIMIT 100;
