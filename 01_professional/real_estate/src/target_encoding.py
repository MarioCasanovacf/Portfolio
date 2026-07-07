"""Fold-safe group estimators: a zip-code mean-target encoder and a
median-by-zipcode baseline.

Both are deliberately hand-rolled rather than pulled from `category_encoders`
(not in the shared venv, and this project doesn't get to add a dependency for
two dozen lines of pandas groupby). Both are also deliberately NOT
scikit-learn `TransformerMixin` subclasses wired into a `Pipeline` — the
encoding needs the target `y`, which a `Pipeline.transform` step does not see
by default, and forcing it through `TransformedTargetRegressor` gymnastics
would obscure the one thing that actually matters here: `fit` must only ever
see the training fold's zip codes and prices, never the test fold's. Calling
code (the notebook, `tests/unit/test_target_encoding.py`) is responsible for
fitting inside the CV loop, on `df.iloc[train_idx]` only — the same discipline
`SimpleImputer` gets automatically from living inside a `Pipeline`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class ZipTargetEncoder:
    """Additive-smoothed mean-target encoding of `zipcode` toward the global
    mean, so that a zip code with only 2-3 training sales does not get a
    wild, overfit average. `smoothing` is the number of "prior" observations
    the global mean counts as; higher = more shrinkage for small groups."""

    def __init__(self, smoothing: float = 10.0):
        self.smoothing = smoothing

    def fit(self, zips: np.ndarray, y: np.ndarray) -> "ZipTargetEncoder":
        self.global_mean_ = float(np.mean(y))
        frame = pd.DataFrame({"zip": np.asarray(zips), "y": np.asarray(y)})
        agg = frame.groupby("zip")["y"].agg(["mean", "count"])
        self.map_ = (
            (agg["mean"] * agg["count"] + self.global_mean_ * self.smoothing)
            / (agg["count"] + self.smoothing)
        )
        return self

    def transform(self, zips: np.ndarray) -> np.ndarray:
        if not hasattr(self, "map_"):
            raise RuntimeError("ZipTargetEncoder.transform called before fit")
        # A zip code unseen at fit time (e.g., held out entirely under a
        # zipcode-blocked CV split) falls back to the global mean — no
        # information about it exists in the training fold to encode.
        return pd.Series(np.asarray(zips)).map(self.map_).fillna(self.global_mean_).to_numpy()


class GroupMedianRegressor:
    """Honest baseline: predict the median target within the group a row
    belongs to (here, zipcode), falling back to the global median for a
    group never seen at fit time. This is the "ask a local appraiser who
    only knows the neighborhood median" baseline every R^2 in this project
    gets measured against."""

    def __init__(self, smoothing: float = 0.0):
        self.smoothing = smoothing  # kept for API symmetry with ZipTargetEncoder; unused (median has no closed-form shrinkage)

    def fit(self, groups: np.ndarray, y: np.ndarray) -> "GroupMedianRegressor":
        self.global_median_ = float(np.median(y))
        frame = pd.DataFrame({"group": np.asarray(groups), "y": np.asarray(y)})
        self.map_ = frame.groupby("group")["y"].median()
        return self

    def predict(self, groups: np.ndarray) -> np.ndarray:
        if not hasattr(self, "map_"):
            raise RuntimeError("GroupMedianRegressor.predict called before fit")
        return pd.Series(np.asarray(groups)).map(self.map_).fillna(self.global_median_).to_numpy()
