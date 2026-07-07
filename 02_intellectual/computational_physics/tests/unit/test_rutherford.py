"""Property tests for the Velocity-Verlet Rutherford scattering integrator.

Invariants:
  * the deflection obeys Rutherford's law tan(theta/2) = a / b (equivalently
    theta = 2 arctan(a/b)), from which dsigma/dOmega ∝ csc^4(theta/2) follows;
  * the binned differential cross section tracks csc^4(theta/2);
  * a symplectic integrator bounds the kinetic-energy drift (elastic scattering).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import spearmanr

from rutherford import coulomb_length, scattering_angles_deg, verlet_integrator

V0 = 2.0   # incoming speed
Q1 = 2.0   # alpha charge
M1 = 4.0   # alpha mass


@pytest.mark.unit
def test_verlet_reproduces_rutherford_angle() -> None:
    """Per-particle deflection follows theta = 2 arctan(a/b) across impact parameters."""
    b = np.linspace(5.0, 40.0, 60)
    n = len(b)
    x = np.full(n, -200.0)
    vx = np.full(n, V0)
    _, _, fvx, fvy = verlet_integrator(x, b.copy(), vx, np.zeros(n), 0.05, 5000, Q1, M1)

    theta = np.abs(scattering_angles_deg(fvx, fvy))
    a = coulomb_length(Q1, M1, V0)
    theta_law = 2.0 * np.degrees(np.arctan(a / b))

    err = np.abs(theta - theta_law)
    # Finite start distance + discretization leave a few-degree systematic; no drift.
    assert err.max() < 5.0
    assert err.mean() < 3.0


@pytest.mark.unit
def test_cross_section_tracks_csc4() -> None:
    """A disk-uniform beam yields a differential cross section ∝ csc^4(theta/2)."""
    rng = np.random.default_rng(42)
    n = 2000
    b_max = 60.0
    # disk-uniform incidence: b^2 uniform -> b = sqrt(U) * b_max
    b = np.sqrt(rng.uniform(0.0, 1.0, n)) * b_max
    y = b * rng.choice([-1.0, 1.0], n)
    x = np.full(n, -250.0)
    _, _, fvx, fvy = verlet_integrator(x, y, np.full(n, V0), np.zeros(n), 0.05, 6000, Q1, M1)

    theta = np.abs(scattering_angles_deg(fvx, fvy))
    bins = np.linspace(10.0, 150.0, 28)
    centers = 0.5 * (bins[1:] + bins[:-1])
    counts, _ = np.histogram(theta, bins=bins)
    d_omega = 2.0 * np.pi * np.sin(np.radians(centers)) * np.radians(bins[1] - bins[0])
    dsig = counts / d_omega
    csc4 = 1.0 / np.sin(np.radians(centers / 2.0)) ** 4

    populated = counts >= 5
    rho, _ = spearmanr(dsig[populated], csc4[populated])
    assert rho >= 0.95  # empirical cross section follows the csc^4 law (rank-monotone)
    # and it falls with angle, as csc^4 does
    rho_angle, _ = spearmanr(dsig[populated], centers[populated])
    assert rho_angle <= -0.9

    # Shape test (not just monotonicity): dsig vs csc^4 must be ~proportional, i.e. a
    # log-log slope near 1. A monotone-but-wrong law — e.g. raw counts with no
    # solid-angle (dOmega) correction — gives slope ~0.76 and fails this bound.
    lx = np.log(csc4[populated])
    ly = np.log(dsig[populated])
    slope = np.polyfit(lx, ly, 1)[0]
    assert 0.85 <= slope <= 1.15
    assert np.corrcoef(lx, ly)[0, 1] >= 0.97


@pytest.mark.unit
def test_velocity_verlet_bounds_energy_drift() -> None:
    """Elastic scattering: each particle returns to its initial speed (symplectic)."""
    b = np.linspace(5.0, 40.0, 60)
    n = len(b)
    x = np.full(n, -200.0)
    vx = np.full(n, V0)
    _, _, fvx, fvy = verlet_integrator(x, b.copy(), vx, np.zeros(n), 0.05, 5000, Q1, M1)

    ke_ratio = (fvx ** 2 + fvy ** 2) / (V0 ** 2)
    assert np.abs(ke_ratio - 1.0).max() < 0.06  # bounded drift, no secular growth
