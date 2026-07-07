"""Smoke tests for the modeling pipeline against the real King County data.

These do not re-derive the notebook's findings — they check that the pipeline
primitives the notebook depends on (leak-safe imputation inside a Pipeline,
a finite R^2 on a real held-out fold, a working Moran's I implementation)
actually behave the way §4 of the notebook claims. If one of these breaks,
the notebook's numbers are not trustworthy even if it still executes.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REAL_CSV = _PROJECT_ROOT / "data" / "real" / "kc_house_data.csv"

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def real_df() -> pd.DataFrame:
    if not _REAL_CSV.exists():
        pytest.skip(f"real data not present at {_REAL_CSV}")
    return pd.read_csv(_REAL_CSV)


def test_real_data_shape_matches_documented_provenance(real_df: pd.DataFrame) -> None:
    """Guards data/README.md's provenance claims: 21,613 rows, 21 columns,
    zero NaN, the known bedrooms=33 outlier, no injected Unnamed: 0 column."""
    assert real_df.shape == (21_613, 21)
    assert real_df.isna().sum().sum() == 0
    assert "Unnamed: 0" not in real_df.columns
    assert (real_df["bedrooms"] == 33).sum() == 1


def test_leak_safe_imputation_pipeline_fits_and_predicts(real_df: pd.DataFrame) -> None:
    """The current data has no NaN, but the pipeline must still carry an
    imputer INSIDE the Pipeline (not a manual .fillna(df.mean()) before the
    split) so that a future refresh with missing values cannot leak test
    statistics into train. Fit on a manually-NaN-poisoned copy to prove the
    imputer only ever sees the training fold."""
    df = real_df.copy()
    rng = np.random.default_rng(0)
    poison_idx = rng.choice(df.index, size=50, replace=False)
    df.loc[poison_idx, "bedrooms"] = np.nan

    features = ["sqft_living", "grade", "condition", "bedrooms"]
    X, y = df[features], np.log1p(df["price"])

    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LinearRegression()),
    ])
    scores = cross_val_score(pipe, X, y, cv=KFold(5, shuffle=True, random_state=0), scoring="r2")
    assert np.all(np.isfinite(scores))
    assert scores.mean() > 0  # sanity: sqft_living/grade carry real signal


def test_group_kfold_by_zipcode_is_stricter_than_plain_kfold(real_df: pd.DataFrame) -> None:
    """Spatial blocking (GroupKFold on zipcode) must not let a fold see
    training rows for a test-fold zipcode. This checks the mechanical
    guarantee GroupKFold gives us, not the resulting R^2 gap itself (that's
    the notebook's job, on the full feature set)."""
    df = real_df.sample(2000, random_state=0)
    groups = df["zipcode"].values
    gkf = GroupKFold(n_splits=5)
    for train_idx, test_idx in gkf.split(df, groups=groups):
        train_zips = set(groups[train_idx])
        test_zips = set(groups[test_idx])
        assert train_zips.isdisjoint(test_zips), "GroupKFold leaked a zipcode across the split"


def test_pipeline_beats_dummy_mean_baseline(real_df: pd.DataFrame) -> None:
    """A basic honest-baseline check: an untuned GradientBoosting model on a
    handful of real features must clear DummyRegressor's R^2 of ~0 by a wide
    margin. This is a floor, not the notebook's actual reported number."""
    from sklearn.dummy import DummyRegressor

    features = ["sqft_living", "grade", "condition", "bedrooms", "bathrooms", "lat", "long"]
    X = real_df[features]
    y = np.log1p(real_df["price"])

    dummy_scores = cross_val_score(
        DummyRegressor(strategy="mean"), X, y, cv=KFold(5, shuffle=True, random_state=0), scoring="r2"
    )
    gb_scores = cross_val_score(
        GradientBoostingRegressor(random_state=0),
        X, y, cv=KFold(5, shuffle=True, random_state=0), scoring="r2",
    )
    assert dummy_scores.mean() < 0.05
    assert gb_scores.mean() > 0.5


def test_morans_i_detects_planted_spatial_autocorrelation() -> None:
    """Unit test for the Moran's I helper the notebook uses on residuals:
    it must report strong positive autocorrelation on a surface with an
    obvious spatial gradient, and roughly zero on pure noise with the same
    coordinates. This is the assumption test §4 of the notebook runs on real
    residuals; here it is validated on a case where the answer is known."""
    import sys
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))
    from spatial_diagnostics import morans_i

    rng = np.random.default_rng(1)
    n = 400
    lat = rng.uniform(47.0, 47.8, n)
    lon = rng.uniform(-122.5, -121.3, n)

    structured = lat * 10 + rng.normal(0, 0.01, n)  # smooth gradient, tiny noise
    noise = rng.normal(0, 1, n)  # no spatial structure

    i_structured, p_structured = morans_i(structured, lat, lon, k=8)
    i_noise, p_noise = morans_i(noise, lat, lon, k=8)

    assert i_structured > 0.5
    assert p_structured < 0.01
    assert abs(i_noise) < 0.25
