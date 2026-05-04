"""Deprecated entry point — kept for backwards compatibility with v0.0.x.

The real implementation now lives in ``quantitative_finance.data.generator``.
Calling this module as a script (``python src/data_generator.py``) will continue
to work but is no longer the recommended path; use ``qfinance generate-data``
instead.
"""

from __future__ import annotations

import warnings

from quantitative_finance.config import get_settings
from quantitative_finance.data.generator import (
    generate_all,
    generate_asset_prices,
    generate_lob_events,
    write_csv,
)

__all__ = [
    "generate_all",
    "generate_asset_prices",
    "generate_lob_events",
    "write_csv",
]

warnings.warn(
    "src/data_generator.py is deprecated; import from quantitative_finance.data.generator "
    "or invoke `qfinance generate-data` instead.",
    DeprecationWarning,
    stacklevel=2,
)


def generate_lob_data(n_events: int = 50_000, start_price: float = 150.0) -> None:
    """Legacy wrapper preserving the v0.0.x signature; delegates to the new generator."""
    settings = get_settings().model_copy(
        update={"lob_n_events": n_events, "lob_start_price": start_price}
    )
    df = generate_lob_events(settings)
    write_csv(df, settings.data_dir / settings.lob_filename, include_index=False)


def generate_asset_prices_correlation(n_assets: int = 50, n_days: int = 1000) -> None:
    """Legacy wrapper preserving the v0.0.x signature; delegates to the new generator."""
    settings = get_settings().model_copy(
        update={"assets_n": n_assets, "assets_n_days": n_days}
    )
    df = generate_asset_prices(settings)
    write_csv(df, settings.data_dir / settings.assets_filename, include_index=True)


if __name__ == "__main__":
    generate_all()
