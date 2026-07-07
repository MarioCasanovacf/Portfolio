"""Tests for the shared feature-engineering function."""

import numpy as np
import pandas as pd
import pytest

from features import BASE_FEATURES, RAW_LOCATION_FEATURES, SEATTLE_CBD, engineer_features

pytestmark = pytest.mark.unit


def _toy_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "date": ["20141013T000000", "20150101T000000"],
        "price": [500_000.0, 750_000.0],
        "yr_built": [1990, 2000],
        "yr_renovated": [0, 2010],
        "sqft_basement": [0, 400],
        "lat": [SEATTLE_CBD[0], 47.7],
        "long": [SEATTLE_CBD[1], -122.0],
    })


def test_engineer_features_adds_expected_columns_and_leaves_input_untouched() -> None:
    df = _toy_frame()
    original_cols = set(df.columns)
    out = engineer_features(df)

    for col in ["year_sold", "month_sold", "age", "has_basement", "has_renovation", "log_price", "dist_cbd"]:
        assert col in out.columns
    # Original frame (and its columns) must not be mutated in place.
    assert set(df.columns) == original_cols
    assert not pd.api.types.is_datetime64_any_dtype(df["date"])  # engineer_features parsed a COPY


def test_age_and_flags_are_correct() -> None:
    out = engineer_features(_toy_frame())
    assert out.loc[0, "year_sold"] == 2014
    assert out.loc[0, "age"] == 2014 - 1990
    assert out.loc[0, "has_basement"] == 0
    assert out.loc[0, "has_renovation"] == 0
    assert out.loc[1, "has_basement"] == 1
    assert out.loc[1, "has_renovation"] == 1


def test_dist_cbd_is_zero_at_the_cbd_itself() -> None:
    out = engineer_features(_toy_frame())
    assert out.loc[0, "dist_cbd"] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[1, "dist_cbd"] > 0


def test_log_price_is_log1p_of_price() -> None:
    out = engineer_features(_toy_frame())
    np.testing.assert_allclose(out["log_price"], np.log1p(out["price"]))


def test_feature_lists_do_not_overlap_and_avoid_the_collinear_column() -> None:
    """sqft_above is deliberately excluded from BASE_FEATURES (see
    data/README.md's collinearity note); this pins that decision so a future
    edit can't silently reintroduce the sqft_above+sqft_basement=sqft_living
    identity."""
    assert "sqft_above" not in BASE_FEATURES
    assert set(BASE_FEATURES).isdisjoint(RAW_LOCATION_FEATURES)
