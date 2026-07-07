/*
 * STAGING SCHEMA — Mexican Legislative Data Pipeline
 * ====================================================
 * Cleaned, deduplicated, and properly typed data. This layer applies:
 *   - Data type casting (VARCHAR dates → DATE/TIMESTAMP)
 *   - Deduplication via ROW_NUMBER windowing
 *   - Null handling and standardization
 *   - Business key generation (surrogate keys via MD5 hash)
 *
 * Design decisions:
 *   - Deduplication uses QUALIFY with ROW_NUMBER — Snowflake-native, avoids subqueries.
 *   - Surrogate keys are deterministic MD5 hashes of business keys for idempotent loads.
 *   - Clustering keys chosen based on typical query patterns (filter by legislature, date).
 */

USE DATABASE LEGISLATIVE_MX;

CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'Cleaned and deduplicated staging layer';

USE SCHEMA STAGING;

-- =============================================================================
-- STAGING VIEWS (materialized from raw via streams or full refresh)
-- =============================================================================

/*
 * stg_votes: Cleaned individual vote records.
 * Source: raw.raw_dipmex_votes
 * Transformations:
 *   - Parse vote_date to DATE type
 *   - Standardize vote_cast to enum-like values: 'FOR', 'AGAINST', 'ABSTAIN', 'ABSENT'
 *   - Deduplicate on (legislature, vote_id, legislator_name)
 *   - Generate surrogate key
 */
CREATE OR REPLACE TABLE stg_votes (
    vote_sk             VARCHAR(32)     NOT NULL COMMENT 'Surrogate key: MD5(legislature|vote_id|legislator_name)',
    legislature         INT             NOT NULL,
    vote_date           DATE            COMMENT 'Parsed vote date',
    vote_id             VARCHAR(100)    NOT NULL,
    legislator_name     VARCHAR(500)    NOT NULL,
    party               VARCHAR(100),
    state               VARCHAR(100),
    district            VARCHAR(100),
    vote_cast           VARCHAR(10)     COMMENT 'Standardized: FOR, AGAINST, ABSTAIN, ABSENT',
    _loaded_at          TIMESTAMP_NTZ
)
CLUSTER BY (legislature, vote_date)
COMMENT = 'Staged individual vote records, deduplicated and typed';

-- Transformation query (run as MERGE or INSERT OVERWRITE)
-- This would be executed by dbt or a Prefect task:
/*
INSERT OVERWRITE INTO staging.stg_votes
SELECT
    MD5(legislature || '|' || vote_id || '|' || legislator_name) AS vote_sk,
    legislature,
    TRY_TO_DATE(vote_date, 'YYYY-MM-DD') AS vote_date,
    vote_id,
    TRIM(legislator_name) AS legislator_name,
    UPPER(TRIM(party)) AS party,
    TRIM(state) AS state,
    TRIM(district) AS district,
    CASE UPPER(TRIM(vote_cast))
        WHEN 'FAVOR'       THEN 'FOR'
        WHEN 'A FAVOR'     THEN 'FOR'
        WHEN 'CONTRA'      THEN 'AGAINST'
        WHEN 'EN CONTRA'   THEN 'AGAINST'
        WHEN 'ABSTENCIÓN'  THEN 'ABSTAIN'
        WHEN 'ABSTENCION'  THEN 'ABSTAIN'
        WHEN 'AUSENTE'     THEN 'ABSENT'
        ELSE UPPER(TRIM(vote_cast))
    END AS vote_cast,
    _loaded_at
FROM raw.raw_dipmex_votes
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY legislature, vote_id, legislator_name
    ORDER BY _loaded_at DESC
) = 1;
*/

/*
 * stg_deputies: Cleaned legislator profiles.
 * Source: raw.raw_dipmex_deputies
 */
CREATE OR REPLACE TABLE stg_deputies (
    deputy_sk           VARCHAR(32)     NOT NULL COMMENT 'Surrogate key: MD5(legislature|legislator_id)',
    legislature         INT             NOT NULL,
    legislator_id       VARCHAR(100)    NOT NULL,
    full_name           VARCHAR(500)    NOT NULL,
    first_name          VARCHAR(200)    COMMENT 'Parsed first name',
    last_name           VARCHAR(300)    COMMENT 'Parsed last name(s)',
    party               VARCHAR(100),
    state               VARCHAR(100),
    district_type       VARCHAR(5)      COMMENT 'MR or RP',
    district_number     VARCHAR(20),
    gender              VARCHAR(1)      COMMENT 'M or F',
    _loaded_at          TIMESTAMP_NTZ
)
CLUSTER BY (legislature, party)
COMMENT = 'Staged legislator profiles, deduplicated and typed';

/*
 * stg_vote_summaries: Aggregate vote results from web scraping.
 * Source: raw.raw_diputados_votes
 */
CREATE OR REPLACE TABLE stg_vote_summaries (
    vote_summary_sk     VARCHAR(32)     NOT NULL COMMENT 'Surrogate key: MD5(legislature|vote_id)',
    legislature         INT             NOT NULL,
    session_date        DATE,
    vote_id             VARCHAR(100)    NOT NULL,
    description         VARCHAR(2000),
    votes_for           INT,
    votes_against       INT,
    abstentions         INT,
    absences            INT,
    total_votes         INT             COMMENT 'Computed: for + against + abstentions',
    approval_rate       FLOAT           COMMENT 'Computed: votes_for / total_votes',
    detail_url          VARCHAR(1000),
    _loaded_at          TIMESTAMP_NTZ
)
CLUSTER BY (legislature, session_date)
COMMENT = 'Staged vote summaries with computed metrics';

-- =============================================================================
-- DATA QUALITY CHECKS (executable as assertions)
-- =============================================================================

-- Check: No null surrogate keys
-- SELECT COUNT(*) FROM staging.stg_votes WHERE vote_sk IS NULL;  -- Expected: 0

-- Check: vote_cast only contains valid values
-- SELECT DISTINCT vote_cast FROM staging.stg_votes
-- WHERE vote_cast NOT IN ('FOR', 'AGAINST', 'ABSTAIN', 'ABSENT');  -- Expected: empty

-- Check: approval_rate between 0 and 1
-- SELECT COUNT(*) FROM staging.stg_vote_summaries
-- WHERE approval_rate < 0 OR approval_rate > 1;  -- Expected: 0
