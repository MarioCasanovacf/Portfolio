"""Main orchestration flow for the Mexican legislative data pipeline.

Architecture:
    capture (scrape sources) → load (raw → DuckDB/Snowflake) → transform (staging → analytics)

Design decisions:
    - Prefect chosen over Airflow for lower operational overhead and Pythonic API.
      A portfolio project doesn't need Airflow's scheduler daemon; Prefect flows are
      regular Python functions that can run locally or in Prefect Cloud.
    - Dagster was considered for its software-defined assets paradigm, but Prefect's
      task-level retries and simpler mental model won for this use case.
    - Each task is idempotent: re-running the flow does not duplicate data.
      Raw loads use INSERT with deduplication; staging uses full refresh (INSERT OVERWRITE).
"""

from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash

from capture.dipmex import DipMexClient
from capture.diputados import DiputadosScraper
from config import get_settings
from loaders.duckdb_loader import DuckDBLoader

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


# =============================================================================
# TASKS — Atomic units of work with retry logic
# =============================================================================


@task(
    name="capture-dipmex",
    retries=2,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    tags=["capture"],
)
def capture_dipmex() -> list[Path]:
    """Download dipMex academic datasets from GitHub.

    Returns:
        List of paths to downloaded CSV files.
    """
    logger = get_run_logger()
    settings = get_settings()

    with DipMexClient(settings.capture) as client:
        paths = client.scrape()
        logger.info(f"dipMex capture complete: {len(paths)} files downloaded")
        return paths


@task(
    name="capture-diputados",
    retries=2,
    retry_delay_seconds=120,
    tags=["capture"],
)
def capture_diputados() -> list[Path]:
    """Scrape voting records from the Chamber of Deputies website.

    Returns:
        List of paths to saved CSV files.
    """
    logger = get_run_logger()
    settings = get_settings()

    with DiputadosScraper(settings.capture) as scraper:
        paths = scraper.scrape()
        logger.info(f"Diputados scrape complete: {len(paths)} files saved")
        return paths


@task(
    name="load-raw-files",
    retries=1,
    retry_delay_seconds=30,
    tags=["load"],
)
def load_raw_files(file_paths: list[Path]) -> dict[str, int]:
    """Load captured CSV files into the raw warehouse layer.

    Determines target table name from the file path convention:
        data/raw/dipmex/votes_64.csv → raw.dipmex_votes_64
        data/raw/diputados/votes_LXVI.csv → raw.diputados_votes_lxvi

    Args:
        file_paths: Paths to raw CSV files from capture tasks.

    Returns:
        Dict mapping table names to row counts loaded.
    """
    logger = get_run_logger()
    results: dict[str, int] = {}

    with DuckDBLoader() as loader:
        for path in file_paths:
            if not path.exists():
                logger.warning(f"File not found, skipping: {path}")
                continue

            # Derive table name from directory/filename structure.
            source = path.parent.name  # e.g., 'dipmex' or 'diputados'
            stem = path.stem.lower()   # e.g., 'votes_64'
            table_name = f"raw_{source}_{stem}"

            rows = loader.load_csv_to_raw(path, table_name)
            results[table_name] = rows
            logger.info(f"Loaded {rows} rows into raw.{table_name}")

    return results


@task(
    name="run-staging-transforms",
    retries=1,
    tags=["transform"],
)
def run_staging_transforms() -> int:
    """Execute staging SQL transformations.

    In a production setup with dbt, this would be `dbt run --select staging`.
    For the DuckDB local environment, we execute SQL files directly.

    Returns:
        Number of SQL statements executed.
    """
    logger = get_run_logger()
    staging_sql = SQL_DIR / "queries" / "staging_transforms.sql"

    if not staging_sql.exists():
        logger.warning("Staging transforms SQL not found, skipping")
        return 0

    with DuckDBLoader() as loader:
        loader.execute_sql_file(staging_sql)
        logger.info("Staging transforms executed")
        return 1


@task(
    name="run-analytics-transforms",
    retries=1,
    tags=["transform"],
)
def run_analytics_transforms() -> int:
    """Execute analytics/dimensional model transforms.

    Returns:
        Number of SQL statements executed.
    """
    logger = get_run_logger()
    analytics_sql = SQL_DIR / "queries" / "analytics_transforms.sql"

    if not analytics_sql.exists():
        logger.warning("Analytics transforms SQL not found, skipping")
        return 0

    with DuckDBLoader() as loader:
        loader.execute_sql_file(analytics_sql)
        logger.info("Analytics transforms executed")
        return 1


@task(
    name="validate-data-quality",
    tags=["quality"],
)
def validate_data_quality() -> dict[str, bool]:
    """Run data quality checks on the warehouse.

    Returns:
        Dict of check names → pass/fail booleans.
    """
    logger = get_run_logger()
    checks: dict[str, bool] = {}

    with DuckDBLoader() as loader:
        # Check 1: Raw tables have data.
        for table in ["raw_dipmex_votes_64", "raw_dipmex_deputies_64"]:
            try:
                count = loader.table_row_count(table)
                checks[f"{table}_has_data"] = count > 0
                logger.info(f"Quality check: {table} has {count} rows")
            except Exception:
                checks[f"{table}_has_data"] = False
                logger.warning(f"Quality check: {table} not found or empty")

    passed = sum(v for v in checks.values())
    total = len(checks)
    logger.info(f"Data quality: {passed}/{total} checks passed")
    return checks


# =============================================================================
# FLOWS — Orchestrated sequences of tasks
# =============================================================================


@flow(
    name="legislative-data-pipeline",
    description="End-to-end pipeline: capture → load → transform → validate",
    retries=0,
)
def legislative_pipeline(
    sources: list[str] | None = None,
    skip_capture: bool = False,
) -> dict[str, object]:
    """Run the full legislative data pipeline.

    Args:
        sources: Which sources to capture ('dipmex', 'diputados'). Defaults to all.
        skip_capture: Skip capture and only run transforms (useful for development).

    Returns:
        Summary dict with results from each stage.
    """
    logger = get_run_logger()
    logger.info("Starting legislative data pipeline")
    sources = sources or ["dipmex", "diputados"]
    results: dict[str, object] = {"sources": sources}

    # Stage 1: Capture
    all_files: list[Path] = []
    if not skip_capture:
        if "dipmex" in sources:
            dipmex_files = capture_dipmex()
            all_files.extend(dipmex_files)

        if "diputados" in sources:
            diputados_files = capture_diputados()
            all_files.extend(diputados_files)

        results["captured_files"] = len(all_files)
        logger.info(f"Capture stage complete: {len(all_files)} files")
    else:
        logger.info("Skipping capture stage")

    # Stage 2: Load raw
    if all_files:
        load_results = load_raw_files(all_files)
        results["loaded_tables"] = load_results
    else:
        results["loaded_tables"] = {}

    # Stage 3: Transform
    staging_result = run_staging_transforms()
    analytics_result = run_analytics_transforms()
    results["transforms"] = {
        "staging": staging_result,
        "analytics": analytics_result,
    }

    # Stage 4: Validate
    quality_results = validate_data_quality()
    results["quality_checks"] = quality_results

    logger.info(f"Pipeline complete: {results}")
    return results


@flow(name="capture-only", description="Run only the capture stage")
def capture_only_flow(sources: list[str] | None = None) -> list[Path]:
    """Run only the capture stage (useful for testing scrapers).

    Args:
        sources: Which sources to capture. Defaults to all.

    Returns:
        List of captured file paths.
    """
    sources = sources or ["dipmex", "diputados"]
    files: list[Path] = []

    if "dipmex" in sources:
        files.extend(capture_dipmex())
    if "diputados" in sources:
        files.extend(capture_diputados())

    return files


if __name__ == "__main__":
    legislative_pipeline()
