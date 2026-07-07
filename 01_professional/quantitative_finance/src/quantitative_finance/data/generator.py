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
    A lightweight matching engine is run during generation: the mid price drifts
    as a slow random walk, new orders are placed around it, and submissions that
    would cross the resting book are emitted as executions against the touch
    instead of additions. This guarantees the resulting event stream, when
    replayed, never produces a crossed book (``best_bid < best_ask`` always).
    Each execution additionally exerts a **permanent price impact** on the mid in
    the aggressor's direction (size-proportional, scaled by ``settings.lob_impact``),
    so signed order flow genuinely leads price — a recoverable Kyle-lambda link
    rather than a mid that wanders independently of trading.

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

    bids: dict[float, int] = {}
    asks: dict[float, int] = {}
    events: list[dict] = []
    mid = float(s.lob_start_price)
    ts_ms = 0

    while len(events) < n:
        ts_ms += int(10 + rng.exponential(5))
        ts = s.lob_start_time + timedelta(milliseconds=ts_ms)
        mid += rng.normal(0, 0.005)

        can_cancel = bool(bids) or bool(asks)
        action = rng.choice(["submit", "cancel"], p=[0.85, 0.15]) if can_cancel else "submit"
        side = "Bid" if rng.random() < 0.5 else "Ask"
        size = max(int(rng.lognormal(np.log(100), 1.0)), 1)
        order_id = rng.bytes(4).hex()

        if action == "submit":
            aggressive = rng.random() < 0.15
            offset = -abs(rng.exponential(0.02)) if aggressive else rng.exponential(0.05)
            if side == "Bid":
                price = round(mid - offset, 2)
                best_ask = min(asks.keys()) if asks else None
                if best_ask is not None and price >= best_ask:
                    take = min(size, asks[best_ask])
                    events.append({
                        "timestamp": ts, "order_id": order_id,
                        "event_type": 3, "side": "Ask",
                        "price": best_ask, "size": take,
                    })
                    asks[best_ask] -= take
                    if asks[best_ask] <= 0:
                        del asks[best_ask]
                    # Buy aggressor lifted the offer -> permanent upward price impact.
                    mid += s.lob_impact * take
                else:
                    events.append({
                        "timestamp": ts, "order_id": order_id,
                        "event_type": 1, "side": "Bid",
                        "price": price, "size": size,
                    })
                    bids[price] = bids.get(price, 0) + size
            else:
                price = round(mid + offset, 2)
                best_bid = max(bids.keys()) if bids else None
                if best_bid is not None and price <= best_bid:
                    take = min(size, bids[best_bid])
                    events.append({
                        "timestamp": ts, "order_id": order_id,
                        "event_type": 3, "side": "Bid",
                        "price": best_bid, "size": take,
                    })
                    bids[best_bid] -= take
                    if bids[best_bid] <= 0:
                        del bids[best_bid]
                    # Sell aggressor hit the bid -> permanent downward price impact.
                    mid -= s.lob_impact * take
                else:
                    events.append({
                        "timestamp": ts, "order_id": order_id,
                        "event_type": 1, "side": "Ask",
                        "price": price, "size": size,
                    })
                    asks[price] = asks.get(price, 0) + size
        else:
            book = bids if side == "Bid" else asks
            if not book:
                book = asks if side == "Bid" else bids
                side = "Ask" if side == "Bid" else "Bid"
            price = float(rng.choice(list(book.keys())))
            take = min(book[price], size)
            events.append({
                "timestamp": ts, "order_id": order_id,
                "event_type": 2, "side": side,
                "price": price, "size": take,
            })
            book[price] -= take
            if book[price] <= 0:
                del book[price]

    df = pd.DataFrame(events)
    log.info("lob.generation.done", rows=len(df))
    return df


#: Number of planted sectors in the synthetic asset universe. Assets are split
#: into contiguous equal-size sectors (Asset_1..k -> sector 0, etc.). The HRP
#: notebook reconstructs this same mapping to validate cluster recovery.
ASSET_N_SECTORS = 5


def asset_sector_ids(n_assets: int, n_sectors: int = ASSET_N_SECTORS) -> np.ndarray:
    """Ground-truth sector membership for the synthetic asset universe.

    Contiguous blocks: with ``n_assets=50`` and ``n_sectors=5`` the mapping is
    Asset_1..10 -> 0, Asset_11..20 -> 1, …. Exposed so the notebook can score
    recovered clusters against the planted structure.
    """
    sector_size = max(n_assets // n_sectors, 1)
    return np.minimum(np.arange(n_assets) // sector_size, n_sectors - 1)


def generate_asset_prices(settings: Settings | None = None) -> pd.DataFrame:
    """Generate synthetic correlated daily prices with a planted sector structure.

    Returns follow a linear **factor model** so the correlation matrix has genuine,
    *recoverable* block structure (rather than a single unstructured random draw):

        r_it = b_market · market_t + b_sector · sectorfactor[sector(i)]_t + b_idio · eps_it

    This induces high within-sector correlation (~0.7) and low between-sector
    correlation (~0.2). Hierarchical clustering recovers the blocks, and the HRP
    notebook validates that recovery against :func:`asset_sector_ids`. Daily returns
    are then rescaled by the configured volatility regimes and prices recovered as
    ``exp(cumsum(returns)) * 100``.

    Returns:
        Wide DataFrame indexed by ``Date``, with one column per asset
        (``Asset_1`` … ``Asset_n``).
    """
    s = settings or get_settings()
    rng = _rng(s.random_seed + 1)
    n, t_days = s.assets_n, s.assets_n_days
    log.info("assets.generation.start", n_assets=n, n_days=t_days)

    sector_id = asset_sector_ids(n)

    # Factor model: one common market factor, one factor per sector, idiosyncratic.
    b_market, b_sector, b_idio = 0.5, 0.8, 0.6
    market = rng.standard_normal(t_days)
    sector_factors = rng.standard_normal((t_days, ASSET_N_SECTORS))
    idio = rng.standard_normal((t_days, n))
    returns = (
        b_market * market[:, None]
        + b_sector * sector_factors[:, sector_id]
        + b_idio * idio
    )

    # Volatility regimes (common market-stress windows), then scale to daily units.
    regime = np.ones(t_days)
    regime[s.high_vol_start : s.high_vol_end] = s.high_vol_multiplier
    regime[s.medium_vol_start : s.medium_vol_end] = s.medium_vol_multiplier
    returns = returns * regime[:, None] * 0.01

    prices = np.exp(np.cumsum(returns, axis=0)) * 100
    dates = [s.assets_start_date + timedelta(days=i) for i in range(t_days)]

    df = pd.DataFrame(prices, columns=[f"Asset_{i + 1}" for i in range(n)])
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
