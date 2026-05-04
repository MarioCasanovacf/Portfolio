"""Centralized configuration.

All settings can be overridden via environment variables prefixed with ``QFINANCE_``,
or via a ``.env`` file in the working directory.

Example:
    QFINANCE_RANDOM_SEED=123 qfinance generate-data --lob
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level settings for the quantitative-finance toolkit."""

    model_config = SettingsConfigDict(
        env_prefix="QFINANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = Field(default="INFO", description="Root logging level.")
    data_dir: Path = Field(default=Path("data"), description="Root directory for generated CSVs.")
    random_seed: int = Field(default=42, ge=0, description="Seed for reproducible generation.")

    lob_n_events: int = Field(default=50_000, ge=1, description="Number of LOB events to synthesize.")
    lob_start_price: float = Field(default=150.0, gt=0, description="Initial mid price for the random walk.")
    lob_start_time: datetime = Field(default=datetime(2025, 1, 1, 9, 30, 0))
    lob_filename: str = Field(default="lob_events_synthetic.csv")

    assets_n: int = Field(default=50, ge=2, description="Number of synthetic assets.")
    assets_n_days: int = Field(default=1000, ge=2, description="Number of trading days simulated.")
    assets_start_date: datetime = Field(default=datetime(2020, 1, 1))
    assets_filename: str = Field(default="correlated_assets_synthetic.csv")
    high_vol_start: int = Field(default=300, ge=0)
    high_vol_end: int = Field(default=400, ge=0)
    high_vol_multiplier: float = Field(default=3.0, gt=0)
    medium_vol_start: int = Field(default=700, ge=0)
    medium_vol_end: int = Field(default=850, ge=0)
    medium_vol_multiplier: float = Field(default=2.0, gt=0)


def get_settings() -> Settings:
    """Return a fresh ``Settings`` instance (re-reads env on each call)."""
    return Settings()
