"""DuckDB loader for local development and testing.

Provides the same interface as the Snowflake loader but targets a local DuckDB
database. This allows full pipeline testing without cloud credentials.

DuckDB was chosen as the local proxy because:
  - Column-oriented like Snowflake (similar query performance characteristics).
  - Supports SQL syntax close to Snowflake (window functions, CTEs, QUALIFY*).
  - Zero infrastructure — single file database.
  - Native Parquet/CSV reading without COPY INTO staging.

* QUALIFY is not natively supported in DuckDB; we use subqueries as equivalent.
"""

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import structlog

from config import WarehouseSettings, get_settings

logger = structlog.get_logger(__name__)


class DuckDBLoader:
    """Load data into a local DuckDB warehouse.

    Mirrors the Snowflake loader interface for backend-agnostic pipeline design.
    """

    def __init__(self, settings: WarehouseSettings | None = None) -> None:
        self.settings = settings or get_settings().warehouse
        self.db_path = self.settings.duckdb_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._initialize_schemas()
        self.log = logger.bind(loader="duckdb", db_path=str(self.db_path))

    def _initialize_schemas(self) -> None:
        """Create schemas matching the Snowflake layer structure."""
        for schema in ("raw", "staging", "analytics"):
            self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    def close(self) -> None:
        """Close the DuckDB connection."""
        self.conn.close()

    def __enter__(self) -> "DuckDBLoader":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def load_csv_to_raw(
        self,
        file_path: Path,
        table_name: str,
        schema: str = "raw",
    ) -> int:
        """Load a CSV file into a raw table, creating the table if needed.

        Uses DuckDB's native CSV reader for performance. Adds metadata columns
        (_source_file, _loaded_at) for lineage tracking.

        Args:
            file_path: Path to the CSV file.
            table_name: Target table name.
            schema: Target schema (default: raw).

        Returns:
            Number of rows loaded.
        """
        qualified_name = f"{schema}.{table_name}"
        self.log.info("loading_csv", file=str(file_path), target=qualified_name)

        # Read CSV and add metadata columns.
        df = pd.read_csv(file_path, dtype=str)
        df["_source_file"] = str(file_path)
        df["_loaded_at"] = pd.Timestamp.now()

        # Create or append to table.
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {qualified_name} AS SELECT * FROM df LIMIT 0")
        self.conn.execute(f"INSERT INTO {qualified_name} SELECT * FROM df")

        row_count = len(df)
        self.log.info("csv_loaded", target=qualified_name, rows=row_count)
        return row_count

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str = "raw",
        mode: str = "append",
    ) -> int:
        """Load a pandas DataFrame into a table.

        Args:
            df: DataFrame to load.
            table_name: Target table name.
            schema: Target schema.
            mode: 'append' or 'replace'.

        Returns:
            Number of rows loaded.
        """
        qualified_name = f"{schema}.{table_name}"
        self.log.info("loading_dataframe", target=qualified_name, rows=len(df), mode=mode)

        if mode == "replace":
            self.conn.execute(f"DROP TABLE IF EXISTS {qualified_name}")
            self.conn.execute(f"CREATE TABLE {qualified_name} AS SELECT * FROM df")
        else:
            self.conn.execute(
                f"CREATE TABLE IF NOT EXISTS {qualified_name} AS SELECT * FROM df LIMIT 0"
            )
            self.conn.execute(f"INSERT INTO {qualified_name} SELECT * FROM df")

        return len(df)

    def execute_sql(self, sql: str) -> duckdb.DuckDBPyRelation:
        """Execute arbitrary SQL against the warehouse.

        Args:
            sql: SQL statement to execute.

        Returns:
            DuckDB relation result.
        """
        return self.conn.sql(sql)

    def execute_sql_file(self, file_path: Path) -> None:
        """Execute a SQL file against the warehouse.

        Splits on semicolons and executes each statement. Skips Snowflake-specific
        syntax (CREATE STREAM, CREATE TASK, FILE FORMAT, STAGE) when running locally.

        Args:
            file_path: Path to the .sql file.
        """
        self.log.info("executing_sql_file", file=str(file_path))
        sql = file_path.read_text(encoding="utf-8")

        # Skip Snowflake-specific statements that DuckDB can't handle.
        snowflake_only = (
            "CREATE OR REPLACE STREAM",
            "CREATE OR REPLACE TASK",
            "CREATE OR REPLACE FILE FORMAT",
            "CREATE OR REPLACE STAGE",
            "USE DATABASE",
            "USE SCHEMA",
            "CREATE DATABASE",
        )

        statements = [s.strip() for s in sql.split(";") if s.strip()]
        executed = 0
        skipped = 0

        for stmt in statements:
            # Skip comments-only blocks.
            lines = [l for l in stmt.split("\n") if not l.strip().startswith("--") and l.strip()]
            if not lines:
                continue

            first_meaningful = " ".join(lines).strip().upper()
            if any(first_meaningful.startswith(kw) for kw in snowflake_only):
                skipped += 1
                continue

            # Skip statements inside block comments.
            if first_meaningful.startswith("/*"):
                skipped += 1
                continue

            try:
                self.conn.execute(stmt)
                executed += 1
            except Exception:
                self.log.warning("sql_statement_skipped", statement=stmt[:100])
                skipped += 1

        self.log.info("sql_file_executed", executed=executed, skipped=skipped)

    def query_to_df(self, sql: str) -> pd.DataFrame:
        """Execute a query and return results as a DataFrame.

        Args:
            sql: SQL query.

        Returns:
            Query results as a pandas DataFrame.
        """
        return self.conn.sql(sql).df()

    def table_row_count(self, table_name: str, schema: str = "raw") -> int:
        """Get the row count of a table.

        Args:
            table_name: Table name.
            schema: Schema name.

        Returns:
            Number of rows.
        """
        result = self.conn.execute(
            f"SELECT COUNT(*) FROM {schema}.{table_name}"
        ).fetchone()
        return result[0] if result else 0
