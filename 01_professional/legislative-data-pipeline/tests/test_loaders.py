"""Tests for the DuckDB loader."""

from pathlib import Path

import pandas as pd
import pytest

from loaders.duckdb_loader import DuckDBLoader
from config import WarehouseSettings


@pytest.fixture
def loader(tmp_path: Path) -> DuckDBLoader:
    """Create a DuckDB loader with a temporary database."""
    settings = WarehouseSettings(duckdb_path=tmp_path / "test.duckdb")
    return DuckDBLoader(settings)


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,party,votes\nAlice,PAN,100\nBob,MORENA,200\n")
    return csv_path


class TestDuckDBLoader:
    """Tests for the DuckDB warehouse loader."""

    def test_schemas_created(self, loader: DuckDBLoader) -> None:
        """Verify raw, staging, and analytics schemas exist."""
        result = loader.conn.execute(
            "SELECT schema_name FROM information_schema.schemata"
        ).fetchall()
        schema_names = {row[0] for row in result}
        assert "raw" in schema_names
        assert "staging" in schema_names
        assert "analytics" in schema_names
        loader.close()

    def test_load_csv_to_raw(self, loader: DuckDBLoader, sample_csv: Path) -> None:
        """CSV files are loaded with metadata columns."""
        rows = loader.load_csv_to_raw(sample_csv, "test_table")
        assert rows == 2

        df = loader.query_to_df("SELECT * FROM raw.test_table")
        assert len(df) == 2
        assert "_source_file" in df.columns
        assert "_loaded_at" in df.columns
        loader.close()

    def test_load_dataframe_append(self, loader: DuckDBLoader) -> None:
        """DataFrames are appended to existing tables."""
        df1 = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        df2 = pd.DataFrame({"a": [3], "b": ["z"]})

        loader.load_dataframe(df1, "append_test")
        loader.load_dataframe(df2, "append_test")

        result = loader.query_to_df("SELECT COUNT(*) AS cnt FROM raw.append_test")
        assert result["cnt"].iloc[0] == 3
        loader.close()

    def test_load_dataframe_replace(self, loader: DuckDBLoader) -> None:
        """Replace mode drops and recreates the table."""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [4, 5]})

        loader.load_dataframe(df1, "replace_test")
        loader.load_dataframe(df2, "replace_test", mode="replace")

        result = loader.query_to_df("SELECT COUNT(*) AS cnt FROM raw.replace_test")
        assert result["cnt"].iloc[0] == 2
        loader.close()

    def test_table_row_count(self, loader: DuckDBLoader, sample_csv: Path) -> None:
        """Row count is accurate after load."""
        loader.load_csv_to_raw(sample_csv, "count_test")
        assert loader.table_row_count("count_test") == 2
        loader.close()

    def test_context_manager(self, tmp_path: Path) -> None:
        """Loader works as a context manager."""
        settings = WarehouseSettings(duckdb_path=tmp_path / "ctx.duckdb")
        with DuckDBLoader(settings) as loader:
            df = pd.DataFrame({"x": [1]})
            loader.load_dataframe(df, "ctx_test")
            assert loader.table_row_count("ctx_test") == 1
