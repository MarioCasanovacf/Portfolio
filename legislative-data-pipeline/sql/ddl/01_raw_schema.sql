/*
 * RAW SCHEMA — Mexican Legislative Data Pipeline
 * ================================================
 * Landing zone for ingested data. Tables mirror the structure of source files
 * with minimal transformation (only metadata columns added).
 *
 * Design decisions:
 *   - VARIANT columns for semi-structured source data (Snowflake-native JSON handling).
 *   - _loaded_at timestamp for auditing and incremental load tracking.
 *   - _source_file for lineage tracing back to raw files.
 *   - No primary keys enforced at this layer; deduplication happens in staging.
 *
 * Compatible with: Snowflake (primary), DuckDB (local dev with minor syntax adjustments).
 */

-- =============================================================================
-- DATABASE AND SCHEMA SETUP
-- =============================================================================

CREATE DATABASE IF NOT EXISTS LEGISLATIVE_MX
    DATA_RETENTION_TIME_IN_DAYS = 7
    COMMENT = 'Mexican legislative data warehouse';

USE DATABASE LEGISLATIVE_MX;

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Raw landing zone — ingested data with minimal transformation';

USE SCHEMA RAW;

-- =============================================================================
-- FILE FORMAT DEFINITIONS
-- =============================================================================

CREATE OR REPLACE FILE FORMAT csv_format
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null', 'NA', 'N/A')
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    COMMENT = 'Standard CSV format for legislative data ingestion';

CREATE OR REPLACE FILE FORMAT json_format
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE
    COMMENT = 'JSON format for semi-structured legislative data';

-- =============================================================================
-- STAGES (Snowflake internal stages for file loading)
-- =============================================================================

CREATE OR REPLACE STAGE raw_stage
    FILE_FORMAT = csv_format
    COMMENT = 'Internal stage for raw legislative data files';

-- =============================================================================
-- RAW TABLES
-- =============================================================================

/*
 * raw_dipmex_votes: Roll-call vote records from the dipMex academic dataset.
 * Source: github.com/emagar/dipMex
 * Grain: One row per legislator per vote event.
 */
CREATE OR REPLACE TABLE raw_dipmex_votes (
    legislature         INT             COMMENT 'Legislature number (e.g., 64, 65, 66)',
    vote_date           VARCHAR(50)     COMMENT 'Date of the vote session',
    vote_id             VARCHAR(100)    COMMENT 'Vote event identifier from source',
    legislator_name     VARCHAR(500)    COMMENT 'Full name of the legislator',
    party               VARCHAR(100)    COMMENT 'Political party abbreviation',
    state               VARCHAR(100)    COMMENT 'State (entidad federativa) represented',
    district            VARCHAR(100)    COMMENT 'Electoral district or plurinominal list',
    vote_cast           VARCHAR(50)     COMMENT 'Vote value: favor, contra, abstención, ausente',
    _source_file        VARCHAR(500)    COMMENT 'Source file path for lineage',
    _loaded_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP() COMMENT 'Ingestion timestamp'
);

/*
 * raw_dipmex_deputies: Legislator profile data from dipMex.
 * Grain: One row per legislator per legislature.
 */
CREATE OR REPLACE TABLE raw_dipmex_deputies (
    legislature         INT             COMMENT 'Legislature number',
    legislator_id       VARCHAR(100)    COMMENT 'Unique legislator identifier from source',
    full_name           VARCHAR(500)    COMMENT 'Full name',
    party               VARCHAR(100)    COMMENT 'Party at time of election',
    state               VARCHAR(100)    COMMENT 'State represented',
    district_type       VARCHAR(50)     COMMENT 'MR (mayoría relativa) or RP (representación proporcional)',
    district_number     VARCHAR(20)     COMMENT 'District number (for MR) or list position (for RP)',
    gender              VARCHAR(10)     COMMENT 'Gender',
    substitute_name     VARCHAR(500)    COMMENT 'Name of substitute legislator (suplente)',
    _source_file        VARCHAR(500)    COMMENT 'Source file path for lineage',
    _loaded_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP() COMMENT 'Ingestion timestamp'
);

/*
 * raw_diputados_votes: Scraped vote summaries from diputados.gob.mx.
 * Grain: One row per vote event (aggregate counts, not individual votes).
 */
CREATE OR REPLACE TABLE raw_diputados_votes (
    legislature         INT             COMMENT 'Legislature number',
    session_date        VARCHAR(50)     COMMENT 'Session date as published',
    vote_id             VARCHAR(100)    COMMENT 'Generated vote identifier',
    description         VARCHAR(2000)   COMMENT 'Description of the matter voted on',
    votes_for           INT             COMMENT 'Total votes in favor',
    votes_against       INT             COMMENT 'Total votes against',
    abstentions         INT             COMMENT 'Total abstentions',
    absences            INT             COMMENT 'Total absences',
    detail_url          VARCHAR(1000)   COMMENT 'URL to individual vote detail page',
    _source_file        VARCHAR(500)    COMMENT 'Source file path for lineage',
    _loaded_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP() COMMENT 'Ingestion timestamp'
);

/*
 * raw_ine_election_results: INE open data election results.
 * Grain: One row per candidate per district per election.
 */
CREATE OR REPLACE TABLE raw_ine_election_results (
    election_year       INT             COMMENT 'Election year',
    election_type       VARCHAR(100)    COMMENT 'Type: presidente, diputados, senadores',
    state               VARCHAR(100)    COMMENT 'State (entidad federativa)',
    district            VARCHAR(100)    COMMENT 'Electoral district',
    section             VARCHAR(50)     COMMENT 'Electoral section (casilla level)',
    party               VARCHAR(100)    COMMENT 'Party or coalition name',
    candidate_name      VARCHAR(500)    COMMENT 'Candidate name',
    votes_received      INT             COMMENT 'Total votes received',
    _source_file        VARCHAR(500)    COMMENT 'Source file path for lineage',
    _loaded_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP() COMMENT 'Ingestion timestamp'
);

-- =============================================================================
-- STREAMS (Change Data Capture for incremental processing)
-- =============================================================================
-- Streams track DML changes on raw tables so the staging layer
-- only processes new/changed rows on each pipeline run.

CREATE OR REPLACE STREAM stream_raw_dipmex_votes
    ON TABLE raw_dipmex_votes
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'CDC stream for incremental processing of dipMex vote data';

CREATE OR REPLACE STREAM stream_raw_dipmex_deputies
    ON TABLE raw_dipmex_deputies
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'CDC stream for incremental processing of dipMex deputy data';

CREATE OR REPLACE STREAM stream_raw_diputados_votes
    ON TABLE raw_diputados_votes
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'CDC stream for incremental processing of scraped vote data';
