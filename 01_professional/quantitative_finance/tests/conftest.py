"""Shared pytest fixtures for the quantitative-finance test suite."""

from __future__ import annotations

import pytest

from quantitative_finance.config import Settings


@pytest.fixture(scope="session")
def small_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    """Settings tuned for fast tests with a session-isolated data directory."""
    data_dir = tmp_path_factory.mktemp("qfinance_data")
    return Settings(
        random_seed=42,
        data_dir=data_dir,
        lob_n_events=200,
        assets_n=5,
        assets_n_days=60,
        high_vol_start=10,
        high_vol_end=20,
        medium_vol_start=30,
        medium_vol_end=40,
    )
