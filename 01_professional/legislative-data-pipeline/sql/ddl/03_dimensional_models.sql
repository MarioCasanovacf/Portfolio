/*
 * DIMENSIONAL MODELS — Mexican Legislative Data Pipeline
 * ========================================================
 * Star schema optimized for legislative analytics.
 *
 * Design decisions:
 *   - Star schema (not snowflake schema) chosen for query simplicity. The dimensional
 *     cardinality is low enough that denormalization costs are negligible.
 *   - SCD Type 2 on dim_legislator to track caucus switches. Mexican legislators
 *     occasionally switch parties mid-term — this is politically significant
 *     and must be captured historically.
 *   - Date dimension is a standard calendar table enriched with Mexican legislative
 *     session metadata (ordinary and extraordinary sessions).
 *   - Grain of fact_vote: one row per legislator per vote event.
 *   - Grain of fact_vote_summary: one row per vote event (aggregate).
 */

USE DATABASE LEGISLATIVE_MX;

CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Dimensional models for legislative analytics (star schema)';

USE SCHEMA ANALYTICS;

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

/*
 * dim_date: Calendar dimension with legislative session metadata.
 * Populated via a generation script; includes Mexican holidays and
 * legislative periods (Sep 1 – Dec 15, Feb 1 – Apr 30).
 */
CREATE OR REPLACE TABLE dim_date (
    date_key            INT             NOT NULL PRIMARY KEY COMMENT 'YYYYMMDD integer key',
    full_date           DATE            NOT NULL,
    year                INT             NOT NULL,
    month               INT             NOT NULL,
    day                 INT             NOT NULL,
    day_of_week         INT             COMMENT '1=Monday, 7=Sunday (ISO)',
    day_name            VARCHAR(15),
    month_name          VARCHAR(15),
    quarter             INT,
    is_weekend          BOOLEAN,
    -- Legislative calendar fields
    legislature         INT             COMMENT 'Active legislature number',
    legislative_year    INT             COMMENT 'Year within the legislature (1-3)',
    session_type        VARCHAR(20)     COMMENT 'ORDINARIO_1, ORDINARIO_2, EXTRAORDINARIO, RECESO',
    is_session_day      BOOLEAN         COMMENT 'Whether Congress is in session'
);

/*
 * dim_legislator: SCD Type 2 for legislator profiles.
 * Tracks party changes over time with effective date ranges.
 *
 * Why SCD2: In the LXIV-LXVI legislatures, multiple high-profile party switches
 * occurred (e.g., defections to MORENA). Accurate party attribution per vote
 * requires temporal tracking.
 */
CREATE OR REPLACE TABLE dim_legislator (
    legislator_key      INT AUTOINCREMENT PRIMARY KEY COMMENT 'Surrogate key (auto)',
    legislator_id       VARCHAR(100)    NOT NULL COMMENT 'Natural business key',
    full_name           VARCHAR(500)    NOT NULL,
    first_name          VARCHAR(200),
    last_name           VARCHAR(300),
    party               VARCHAR(100)    NOT NULL COMMENT 'Party at this point in time',
    state               VARCHAR(100),
    district_type       VARCHAR(5),
    district_number     VARCHAR(20),
    gender              VARCHAR(1),
    legislature         INT             NOT NULL,
    -- SCD Type 2 fields
    effective_from      DATE            NOT NULL,
    effective_to        DATE            DEFAULT '9999-12-31' COMMENT 'Open-ended for current record',
    is_current          BOOLEAN         DEFAULT TRUE,
    _hash               VARCHAR(32)     COMMENT 'MD5 of tracked attributes for change detection'
);

/*
 * dim_party: Political party reference.
 * Relatively static; updated when new parties are registered or alliances change.
 */
CREATE OR REPLACE TABLE dim_party (
    party_key           INT AUTOINCREMENT PRIMARY KEY,
    party_code          VARCHAR(20)     NOT NULL UNIQUE COMMENT 'Official abbreviation (PAN, PRI, MORENA, etc.)',
    party_name          VARCHAR(200)    NOT NULL COMMENT 'Full official name',
    ideology_spectrum   VARCHAR(20)     COMMENT 'LEFT, CENTER_LEFT, CENTER, CENTER_RIGHT, RIGHT',
    founded_year        INT,
    is_active           BOOLEAN         DEFAULT TRUE
);

-- Seed data for major parties
INSERT INTO dim_party (party_code, party_name, ideology_spectrum, founded_year, is_active)
VALUES
    ('MORENA', 'Movimiento Regeneración Nacional', 'LEFT', 2014, TRUE),
    ('PAN', 'Partido Acción Nacional', 'CENTER_RIGHT', 1939, TRUE),
    ('PRI', 'Partido Revolucionario Institucional', 'CENTER', 1929, TRUE),
    ('PRD', 'Partido de la Revolución Democrática', 'CENTER_LEFT', 1989, TRUE),
    ('PVEM', 'Partido Verde Ecologista de México', 'CENTER', 1986, TRUE),
    ('PT', 'Partido del Trabajo', 'LEFT', 1990, TRUE),
    ('MC', 'Movimiento Ciudadano', 'CENTER_LEFT', 1999, TRUE),
    ('SP', 'Sin Partido (Independiente)', 'CENTER', NULL, TRUE);

/*
 * dim_committee: Legislative committee reference.
 * Committees are where the real legislative work happens.
 */
CREATE OR REPLACE TABLE dim_committee (
    committee_key       INT AUTOINCREMENT PRIMARY KEY,
    committee_id        VARCHAR(100)    NOT NULL,
    committee_name      VARCHAR(500)    NOT NULL,
    committee_type      VARCHAR(50)     COMMENT 'ORDINARIA, ESPECIAL, BICAMERAL',
    chamber             VARCHAR(20)     COMMENT 'DIPUTADOS, SENADO, BICAMERAL',
    legislature         INT
);

-- =============================================================================
-- FACT TABLES
-- =============================================================================

/*
 * fact_vote: Individual legislator votes.
 * Grain: One row per legislator per vote event.
 * This is the primary analytical table — supports party cohesion analysis,
 * legislator scoring, coalition pattern detection.
 */
CREATE OR REPLACE TABLE fact_vote (
    vote_key            INT AUTOINCREMENT PRIMARY KEY,
    -- Dimension keys
    date_key            INT             REFERENCES dim_date(date_key),
    legislator_key      INT             REFERENCES dim_legislator(legislator_key),
    -- Degenerate dimensions
    legislature         INT             NOT NULL,
    vote_event_id       VARCHAR(100)    NOT NULL COMMENT 'Links to fact_vote_summary',
    -- Measures
    vote_cast           VARCHAR(10)     NOT NULL COMMENT 'FOR, AGAINST, ABSTAIN, ABSENT',
    is_affirmative      BOOLEAN         COMMENT 'TRUE if vote_cast = FOR',
    is_present          BOOLEAN         COMMENT 'TRUE if vote_cast != ABSENT'
)
CLUSTER BY (legislature, date_key)
COMMENT = 'Individual legislator votes — grain: one per legislator per vote event';

/*
 * fact_vote_summary: Aggregate vote outcomes.
 * Grain: One row per vote event.
 * Used for high-level legislative productivity analysis and approval rate trends.
 */
CREATE OR REPLACE TABLE fact_vote_summary (
    vote_summary_key    INT AUTOINCREMENT PRIMARY KEY,
    -- Dimension keys
    date_key            INT             REFERENCES dim_date(date_key),
    -- Degenerate dimensions
    legislature         INT             NOT NULL,
    vote_event_id       VARCHAR(100)    NOT NULL UNIQUE,
    description         VARCHAR(2000),
    -- Measures
    votes_for           INT             NOT NULL DEFAULT 0,
    votes_against       INT             NOT NULL DEFAULT 0,
    abstentions         INT             NOT NULL DEFAULT 0,
    absences            INT             NOT NULL DEFAULT 0,
    total_present       INT             COMMENT 'Computed: for + against + abstentions',
    total_eligible      INT             COMMENT 'Computed: total_present + absences',
    approval_rate       FLOAT           COMMENT 'Computed: votes_for / total_present',
    is_approved         BOOLEAN         COMMENT 'TRUE if approval_rate > 0.5 (simple majority)',
    requires_qualified  BOOLEAN         DEFAULT FALSE COMMENT 'TRUE if constitutional reform (2/3 needed)',
    detail_url          VARCHAR(1000)
)
CLUSTER BY (legislature, date_key)
COMMENT = 'Aggregate vote outcomes — grain: one per vote event';

-- =============================================================================
-- ANALYTICAL VIEWS
-- =============================================================================

/*
 * Party cohesion per vote: measures how unified a party votes.
 * Cohesion = max(for_pct, against_pct) — a perfectly unified party scores 1.0.
 */
CREATE OR REPLACE VIEW v_party_cohesion AS
SELECT
    fv.legislature,
    fv.vote_event_id,
    dl.party,
    dd.full_date AS vote_date,
    COUNT(*) AS party_legislators_present,
    SUM(CASE WHEN fv.vote_cast = 'FOR' THEN 1 ELSE 0 END) AS votes_for,
    SUM(CASE WHEN fv.vote_cast = 'AGAINST' THEN 1 ELSE 0 END) AS votes_against,
    SUM(CASE WHEN fv.vote_cast = 'ABSTAIN' THEN 1 ELSE 0 END) AS abstentions,
    GREATEST(
        votes_for::FLOAT / NULLIF(party_legislators_present, 0),
        votes_against::FLOAT / NULLIF(party_legislators_present, 0)
    ) AS cohesion_score
FROM fact_vote fv
JOIN dim_legislator dl ON fv.legislator_key = dl.legislator_key
JOIN dim_date dd ON fv.date_key = dd.date_key
WHERE fv.vote_cast != 'ABSENT'
GROUP BY fv.legislature, fv.vote_event_id, dl.party, dd.full_date;

/*
 * Legislator attendance rate: key indicator of legislative engagement.
 */
CREATE OR REPLACE VIEW v_legislator_attendance AS
SELECT
    dl.legislator_id,
    dl.full_name,
    dl.party,
    dl.legislature,
    COUNT(*) AS total_vote_events,
    SUM(CASE WHEN fv.is_present THEN 1 ELSE 0 END) AS present_count,
    present_count::FLOAT / NULLIF(total_vote_events, 0) AS attendance_rate
FROM fact_vote fv
JOIN dim_legislator dl ON fv.legislator_key = dl.legislator_key
GROUP BY dl.legislator_id, dl.full_name, dl.party, dl.legislature;

-- =============================================================================
-- TASKS (Snowflake scheduled execution for incremental refresh)
-- =============================================================================

/*
 * Task to refresh staging → analytics on a schedule.
 * In production, this would be triggered by Prefect after raw load completes.
 * Shown here to demonstrate Snowflake-native scheduling capability.
 */
-- CREATE OR REPLACE TASK refresh_analytics
--     WAREHOUSE = COMPUTE_WH
--     SCHEDULE = 'USING CRON 0 6 * * * America/Mexico_City'
--     COMMENT = 'Daily refresh of dimensional models from staging'
-- AS
--     CALL sp_refresh_dimensional_models();
