"""Tests for the fold-safe zip target encoder and the median-by-zip baseline.

The property that matters most for this project's honesty claims is the
"unseen group falls back to the global statistic" behavior — that is exactly
what makes the zip-blocked CV result in the notebook (§5) mean what it claims
to mean, rather than silently leaking group averages across the split.
"""

import numpy as np
import pytest

from target_encoding import GroupMedianRegressor, ZipTargetEncoder

pytestmark = pytest.mark.unit


def test_zip_target_encoder_recovers_group_means_with_enough_data() -> None:
    zips = np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2] * 20)
    y = np.where(zips == 1, 10.0, 20.0) + np.random.default_rng(0).normal(0, 0.01, len(zips))
    enc = ZipTargetEncoder(smoothing=1.0).fit(zips, y)
    encoded = enc.transform(zips)
    assert encoded[zips == 1].mean() == pytest.approx(10.0, abs=0.1)
    assert encoded[zips == 2].mean() == pytest.approx(20.0, abs=0.1)


def test_zip_target_encoder_shrinks_small_groups_toward_global_mean() -> None:
    zips = np.array([1] * 1 + [2] * 200)
    y = np.array([1000.0] + [10.0] * 200)  # zip 1 is a single wild outlier sale
    enc = ZipTargetEncoder(smoothing=10.0).fit(zips, y)
    encoded_zip1 = enc.transform(np.array([1]))[0]
    # With smoothing=10 and n=1, the single-sale zip's encoding should sit far
    # below its raw mean (1000) — the whole point of additive smoothing.
    assert encoded_zip1 < 500


def test_zip_target_encoder_falls_back_to_global_mean_for_unseen_zip() -> None:
    zips_train = np.array([1, 1, 1, 2, 2, 2])
    y_train = np.array([10.0, 12.0, 11.0, 20.0, 22.0, 21.0])
    enc = ZipTargetEncoder().fit(zips_train, y_train)
    unseen_encoded = enc.transform(np.array([999]))[0]
    assert unseen_encoded == pytest.approx(enc.global_mean_)


def test_group_median_regressor_predicts_group_median_and_falls_back_for_unseen() -> None:
    groups = np.array([1, 1, 1, 2, 2, 2])
    y = np.array([10.0, 20.0, 30.0, 100.0, 200.0, 300.0])  # medians: 20, 200
    reg = GroupMedianRegressor().fit(groups, y)
    preds = reg.predict(np.array([1, 2, 999]))
    assert preds[0] == pytest.approx(20.0)
    assert preds[1] == pytest.approx(200.0)
    assert preds[2] == pytest.approx(np.median(y))  # global fallback
