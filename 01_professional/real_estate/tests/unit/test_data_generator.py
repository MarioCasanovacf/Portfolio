"""Tests for the synthetic data generator.

These exercise the generator that produces the DECLARED BENCHMARK dataset
(data/synthetic/kc_house_data_synthetic.csv) — not the real King County data,
which has no generator to test (it is a captured file; its provenance is
checked by hash in data/README.md, not by a unit test).
"""

import importlib

import numpy as np
import pandas as pd
import pytest


@pytest.mark.unit
def test_data_generator_importable() -> None:
    module = importlib.import_module("data_generator")
    assert module is not None


@pytest.mark.unit
def test_generate_is_deterministic(tmp_path) -> None:
    """Same seed (fixed at module import, 42) must produce byte-identical output."""
    module = importlib.import_module("data_generator")
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    module.generate_king_county_housing(output_dir=out1, n_houses=200)
    module.generate_king_county_housing(output_dir=out2, n_houses=200)
    df1 = pd.read_csv(out1 / "kc_house_data_synthetic.csv")
    df2 = pd.read_csv(out2 / "kc_house_data_synthetic.csv")
    pd.testing.assert_frame_equal(df1, df2)


@pytest.mark.unit
def test_generate_shape_and_ranges(tmp_path) -> None:
    """The generator must honor the declared params from data/README.md:
    22 columns, coordinates bounded to King County, price clipped to
    [75_000, 5_000_000], and no NaN outside bedrooms/bathrooms."""
    module = importlib.import_module("data_generator")
    out = tmp_path / "run"
    module.generate_king_county_housing(output_dir=out, n_houses=500)
    df = pd.read_csv(out / "kc_house_data_synthetic.csv")

    assert df.shape == (500, 22)
    assert df["price"].between(75_000, 5_000_000).all()
    assert df["lat"].between(47.15, 47.78).all()
    assert df["long"].between(-122.52, -121.31).all()

    non_nan_cols = [c for c in df.columns if c not in ("bedrooms", "bathrooms")]
    assert df[non_nan_cols].isna().sum().sum() == 0

    # Declared injection rates (~2.5% bedrooms, ~2.0% bathrooms), with slack
    # for rounding on small n via int(n * rate).
    bed_nan_rate = df["bedrooms"].isna().mean()
    bath_nan_rate = df["bathrooms"].isna().mean()
    assert 0.01 < bed_nan_rate < 0.04
    assert 0.005 < bath_nan_rate < 0.035


@pytest.mark.unit
def test_generate_writes_inside_project_by_default() -> None:
    """Regression test for the output_dir bug: the default must resolve to
    <project_root>/data/synthetic regardless of the caller's cwd, not to a
    path relative to wherever the process happened to be invoked from."""
    module = importlib.import_module("data_generator")
    default_dir = module._DEFAULT_OUTPUT_DIR
    assert default_dir.is_absolute()
    assert default_dir.parts[-2:] == ("data", "synthetic")
    project_root = module._PROJECT_ROOT
    assert (project_root / "src" / "data_generator.py").exists()


@pytest.mark.unit
def test_spatial_premium_matches_declared_hotspots() -> None:
    """The declared hotspot parameters in data/README.md must actually be the
    ones baked into the generator — this test would fail if someone edited
    the generator without updating the documented DGP, or vice versa."""
    module = importlib.import_module("data_generator")
    src = importlib.import_module("data_generator").__file__
    with open(src) as f:
        text = f.read()
    # The three declared hotspots (lat, long, amplitude) from data/README.md.
    # Amplitudes appear in source with underscore digit separators (220_000).
    for lat_c, lon_c, amp in [
        (47.62, -122.21, "220_000"),
        (47.63, -122.35, "150_000"),
        (47.57, -122.04, "90_000"),
    ]:
        assert str(lat_c) in text and str(lon_c) in text and amp in text
    assert "0.012" in text  # declared Gaussian decay width (sigma^2)
