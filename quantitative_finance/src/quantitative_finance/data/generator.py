"""Synthetic data generation for LOB events and correlated asset prices.

Both generators use ``numpy.random.default_rng`` (modern Generator API) for
thread-safe, reproducible randomness. Outputs are written via the small
:func:`write_csv` helper which creates parent directories as needed.

Backwards-incompatibility note for v0.1.0:
    Previous versions used ``uuid.uuid4()`` for ``order_id``, which is
    non-reproducible. v0.1.0 derives ``order_id`` from the seeded RNG so the
    full DataFrame is bit-identical across runs with the same seed.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import structlog

from quantitative_finance.config import Settings, get_settings

log = structlog.get_logger(__name__)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def generate_lob_events(settings: Settings | None = None) -> pd.DataFrame:
    """Generate synthetic Level-2 tick-by-tick Limit Order Book events.

    Reproduces the dataset consumed by ``notebooks/01_LOB_Reconstruction.ipynb``.
    Events are sampled around a random-walk mid price; sides are uniformly
    Bid/Ask; sizes follow a lognormal distribution truncated at 1.

    Args:
        settings: Optional override. Falls back to environment-loaded settings.

    Returns:
        DataFrame with columns ``timestamp``, ``order_id``, ``event_type``,
        ``side``, ``price``, ``size``. Rows are time-ordered by event index.
    """
    s = settings or get_settings()
    rng = _rng(s.random_seed)
    n = s.lob_n_events
    log.info("lob.generation.start", n_events=n, start_price=s.lob_start_price)

    jitter = rng.exponential(5, n).astype(int)
    timestamps = [
        s.lob_start_time + timedelta(milliseconds=int(i * 10 + jitter[i])) for i in range(n)
    ]

    price_changes = rng.normal(0, 0.01, n)
    mid_prices = s.lob_start_price + np.cumsum(price_changes)

    event_types = rng.choice([1, 2, 3], size=n, p=[0.7, 0.2, 0.1])
    sides = rng.choice(["Bid", "Ask"], size=n)
    sizes = np.maximum(rng.lognormal(np.log(100), 1.0, n).astype(int), 1)
    spreads = rng.uniform(0.01, 0.05, n)

    prices = np.where(sides == "Bid", mid_prices - spreads / 2, mid_prices + spreads / 2)
    prices = np.round(prices, 2)

    order_ids = [rng.bytes(4).hex() for _ in range(n)]

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "order_id": order_ids,
            "event_type": event_types,
            "side": sides,
            "price": prices,
            "size": sizes,
        }
    )
    log.info("lob.generation.done", rows=len(df))
    return df


def generate_asset_prices(settings: Settings | None = None) -> pd.DataFrame:
    """Generate synthetic correlated daily prices for portfolio analytics.

    A random positive-definite correlation matrix is drawn, multivariate-normal
    daily returns are sampled and rescaled by the configured volatility regimes,
    and prices are recovered as ``exp(cumsum(returns)) * 100``.

    Returns:
        Wide DataFrame indexed by ``Date``, with one column per asset
        (``Asset_1`` … ``Asset_n``).
    """
    s = settings or get_settings()
    rng = _rng(s.random_seed + 1)
    log.info("assets.generation.start", n_assets=s.assets_n, n_days=s.assets_n_days)

    a = rng.standard_normal((s.assets_n, s.assets_n))
    cov_matrix = a @ a.T
    diag = np.sqrt(np.diag(cov_matrix))
    corr = cov_matrix / np.outer(diag, diag)

    returns = rng.multivariate_normal(np.zeros(s.assets_n), corr, size=s.assets_n_days)

    regime = np.ones(s.assets_n_days)
    regime[s.high_vol_start : s.high_vol_end] = s.high_vol_multiplier
    regime[s.medium_vol_start : s.medium_vol_end] = s.medium_vol_multiplier
    returns = returns * regime[:, None] * 0.01

    prices = np.exp(np.cumsum(returns, axis=0)) * 100
    dates = [s.assets_start_date + timedelta(days=i) for i in range(s.assets_n_days)]

    df = pd.DataFrame(prices, columns=[f"Asset_{i + 1}" for i in range(s.assets_n)])
    df["Date"] = dates
    df = df.set_index("Date")

    log.info("assets.generation.done", rows=len(df))
    return df


def write_csv(df: pd.DataFrame, path: Path, *, include_index: bool = False) -> Path:
    """Write a DataFrame to CSV, creating parent directories as needed.

    Args:
        df: DataFrame to write.
        path: Destination file path.
        include_index: Whether to write the DataFrame index as the first column.

    Returns:
        The absolute path written (useful for logging and idempotence checks).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=include_index)
    log.info("csv.write", path=str(path), rows=len(df))
    return path.resolve()


def generate_all(settings: Settings | None = None) -> dict[str, Path]:
    """Generate both LOB and asset CSVs, returning a mapping of name → path.

    Outputs are written under ``settings.data_dir`` using the configured filenames.
    """
    s = settings or get_settings()
    lob_df = generate_lob_events(s)
    assets_df = generate_asset_prices(s)
    return {
        "lob": write_csv(lob_df, s.data_dir / s.lob_filename, include_index=False),
        "assets": write_csv(assets_df, s.data_dir / s.assets_filename, include_index=True),
    }
