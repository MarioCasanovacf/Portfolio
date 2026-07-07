"""Property tests for the Crank-Nicolson Schrodinger solver.

Invariants:
  * the scheme is unitary, so the probability norm is conserved exactly;
  * once the lobes separate, transmission + reflection account for ~all of the
    probability (T + R ≈ 1), the conservation the tunneling reading relies on.
A synthetic rectangular barrier reproduces the notebook's calibrated scenario with
no data file.
"""

from __future__ import annotations

import numpy as np
import pytest

from schrodinger import (
    build_cn_operators,
    gaussian_wave_packet,
    probability_norm,
    propagate,
    reflection_probability,
    transmission_probability,
)


def _scenario():
    """Notebook-equivalent setup: packet at x=-2, E=k0^2=25 below a V0=50 barrier on [0.5, 1.0]."""
    x = np.linspace(-5.0, 5.0, 1000)
    dx = x[1] - x[0]
    V = np.where((x >= 0.5) & (x <= 1.0), 50.0, 0.0)
    psi0 = gaussian_wave_packet(x, x0=-2.0, sigma=0.25, k0=5.0, dx=dx)
    return x, dx, V, psi0


@pytest.mark.unit
def test_crank_nicolson_conserves_norm() -> None:
    x, dx, V, psi0 = _scenario()
    n0 = probability_norm(psi0, dx)
    solver, M_R = build_cn_operators(x, V, dt=0.005)
    _, history = propagate(psi0, solver, M_R, steps=100, snap_every=20)

    # Unitary evolution: every snapshot integrates to the initial probability.
    for density in history:
        assert np.isclose(np.sum(density) * dx, n0, atol=1e-6)
    assert np.isclose(n0, 1.0, atol=1e-9)  # the packet was normalized


@pytest.mark.unit
def test_transmission_plus_reflection_sum_to_one() -> None:
    x, dx, V, psi0 = _scenario()
    solver, M_R = build_cn_operators(x, V, dt=0.005)
    psi_f, _ = propagate(psi0, solver, M_R, steps=100, snap_every=20)

    T = transmission_probability(psi_f, x, dx, x_min=1.0)
    R = reflection_probability(psi_f, x, dx, x_max=0.5)
    barrier = float(np.sum(np.abs(psi_f[(x >= 0.5) & (x <= 1.0)]) ** 2) * dx)

    # Exact partition of the conserved norm, and the physical T + R ≈ 1 reading.
    assert np.isclose(T + R + barrier, probability_norm(psi_f, dx), atol=1e-9)
    assert np.isclose(T + R, 1.0, atol=0.02)


@pytest.mark.unit
def test_tunneling_is_partial_and_subunitary() -> None:
    x, dx, V, psi0 = _scenario()
    solver, M_R = build_cn_operators(x, V, dt=0.005)
    psi_f, _ = propagate(psi0, solver, M_R, steps=100, snap_every=20)

    T = transmission_probability(psi_f, x, dx, x_min=1.0)
    R = reflection_probability(psi_f, x, dx, x_max=0.5)
    # E = k0^2 = 25 < V0 = 50: genuine but partial tunneling, most of the packet reflects.
    assert 0.0 < T < R < 1.0
