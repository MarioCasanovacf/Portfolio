"""Unit and integration tests for ``quantitative_finance.data.generator``."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from quantitative_finance.config import Settings
from quantitative_finance.data.generator import (
    generate_all,
    generate_asset_prices,
    generate_lob_events,
    write_csv,
)


@pytest.mark.unit
def test_lob_shape(small_settings: Settings) -> None:
    df = generate_lob_events(small_settings)
    assert len(df) == small_settings.lob_n_events
    assert set(df.columns) == {"timestamp", "order_id", "event_type", "side", "price", "size"}


@pytest.mark.unit
def test_lob_values_in_expected_ranges(small_settings: Settings) -> None:
    df = generate_lob_events(small_settings)
    assert df["price"].gt(0).all()
    assert df["size"].ge(1).all()
    assert df["event_type"].isin([1, 2, 3]).all()
    assert df["side"].isin(["Bid", "Ask"]).all()
    assert df["order_id"].str.len().eq(8).all()


@pytest.mark.unit
def test_lob_deterministic(small_settings: Settings) -> None:
    df1 = generate_lob_events(small_settings)
    df2 = generate_lob_events(small_settings)
    pd.testing.assert_frame_equal(df1, df2)


@pytest.mark.unit
def test_lob_different_seeds_diverge(small_settings: Settings) -> None:
    other = small_settings.model_copy(update={"random_seed": 999})
    df1 = generate_lob_events(small_settings)
    df2 = generate_lob_events(other)
    assert not df1.equals(df2)


@pytest.mark.unit
def test_assets_shape(small_settings: Settings) -> None:
    df = generate_asset_prices(small_settings)
    assert df.shape == (small_settings.assets_n_days, small_settings.assets_n)
    assert df.columns.tolist() == [f"Asset_{i + 1}" for i in range(small_settings.assets_n)]
    assert df.index.name == "Date"


@pytest.mark.unit
def test_assets_positive_prices(small_settings: Settings) -> None:
    df = generate_asset_prices(small_settings)
    assert (df > 0).all().all()


@pytest.mark.unit
def test_assets_deterministic(small_settings: Settings) -> None:
    df1 = generate_asset_prices(small_settings)
    df2 = generate_asset_prices(small_settings)
    pd.testing.assert_frame_equal(df1, df2)


@pytest.mark.unit
@pytest.mark.parametrize("n_events", [1, 10, 100])
def test_lob_arbitrary_size(small_settings: Settings, n_events: int) -> None:
    s = small_settings.model_copy(update={"lob_n_events": n_events})
    df = generate_lob_events(s)
    assert len(df) == n_events


@pytest.mark.integration
def test_generate_all_writes_files(small_settings: Settings, tmp_path: Path) -> None:
    s = small_settings.model_copy(update={"data_dir": tmp_path})
    paths = generate_all(s)
    assert "lob" in paths and "assets" in paths
    assert paths["lob"].exists() and paths["assets"].exists()
    assert paths["lob"].stat().st_size > 0
    assert paths["assets"].stat().st_size > 0


@pytest.mark.integration
def test_write_csv_creates_parent_dir(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested" / "out.csv"
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    written = write_csv(df, nested)
    assert written.exists()
    assert pd.read_csv(written).equals(df)


@pytest.mark.integration
def test_idempotent_runs(small_settings: Settings, tmp_path: Path) -> None:
    """Two consecutive runs of ``generate_all`` produce identical CSV bytes."""
    s = small_settings.model_copy(update={"data_dir": tmp_path})
    paths1 = generate_all(s)
    bytes1 = paths1["lob"].read_bytes()
    paths2 = generate_all(s)
    bytes2 = paths2["lob"].read_bytes()
    assert bytes1 == bytes2
