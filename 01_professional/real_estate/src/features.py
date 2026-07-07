"""Feature engineering shared by the real and synthetic (benchmark) frames.

Kept as one importable function so that the notebook and the test suite run
the exact same transformation on both datasets — the same reason the DGP
warning lives next to `generate_king_county_housing`: nobody should have to
trust that the notebook's markdown accurately describes what a code cell did
somewhere above it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Downtown Seattle (CBD), used as the fixed reference point for `dist_cbd`.
SEATTLE_CBD = (47.6062, -122.3321)

# The additive, non-location feature set. Deliberately excludes `sqft_above`
# (see data/README.md and the VIF check in the notebook): `sqft_above +
# sqft_basement == sqft_living` exactly, so keeping all three manufactures a
# perfect linear dependency. `sqft_basement` is kept because it carries
# information `sqft_living` alone does not (whether/how much of the house is
# below grade); `sqft_above` is the redundant one once both of those exist.
BASE_FEATURES = [
    "bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors",
    "waterfront", "view", "condition", "grade", "sqft_basement",
    "sqft_living15", "sqft_lot15", "age", "has_basement", "has_renovation",
    "year_sold", "month_sold",
]

# Raw, non-memorized location features: smooth functions of coordinates that
# a model could in principle apply to a ZIP code it has never seen. Contrast
# with zip-code target encoding (src/target_encoding.py), which cannot.
RAW_LOCATION_FEATURES = ["lat", "long", "dist_cbd"]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the engineered columns both the real and synthetic frames need:
    `year_sold`, `month_sold`, `age`, `has_basement`, `has_renovation`,
    `dist_cbd`, `log_price`. Leaves every input column untouched."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"].astype(str).str[:8], format="%Y%m%d")
    df["year_sold"] = df["date"].dt.year
    df["month_sold"] = df["date"].dt.month
    df["age"] = (df["year_sold"] - df["yr_built"]).clip(lower=0)
    df["has_basement"] = (df["sqft_basement"] > 0).astype(int)
    df["has_renovation"] = (df["yr_renovated"] > 0).astype(int)
    df["log_price"] = np.log1p(df["price"])
    lat_c, lon_c = SEATTLE_CBD
    df["dist_cbd"] = np.sqrt((df["lat"] - lat_c) ** 2 + (df["long"] - lon_c) ** 2)
    return df
