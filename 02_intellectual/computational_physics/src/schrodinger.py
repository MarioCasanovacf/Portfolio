"""Crank-Nicolson solver for the 1-D time-dependent Schrodinger equation.

Units: hbar = 2m = 1, so a plane wave of momentum k has energy E = k^2. The scheme
is unitary by construction, so the total probability is conserved exactly. These
functions are imported by ``notebooks/02_Schrodinger_Crank_Nicolson.ipynb`` so the
propagated wave packet and the unit tests share one implementation.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sparse
import scipy.sparse.linalg as spla


def gaussian_wave_packet(x: np.ndarray, x0: float, sigma: float, k0: float,
                         dx: float) -> np.ndarray:
    """A normalized Gaussian packet centred at x0 with central momentum k0."""
    psi_0 = np.exp(-0.5 * ((x - x0) / sigma) ** 2) * np.exp(1j * k0 * x)
    # Unitary normalization (the integral of probability must be exactly 1)
    norm = np.sum(np.abs(psi_0) ** 2) * dx
    return psi_0 / np.sqrt(norm)


def build_cn_operators(x: np.ndarray, V: np.ndarray, dt: float):
    """Build the Crank-Nicolson operators for potential V on grid x.

    Returns ``(solver, M_R)`` where ``solver`` is a factorized direct solver for
    ``M_L`` and one step is ``psi <- solver(M_R @ psi)``, i.e. solving
    ``(I + i dt/2 H) psi^{n+1} = (I - i dt/2 H) psi^{n}``.
    """
    N = len(x)
    dx = x[1] - x[0]

    # Laplacian Coefficient
    alpha = 1.0 / (dx ** 2)
    d0 = 2.0 * alpha + V            # Main diagonal: 2/dx^2 + V(x)
    d1 = -alpha * np.ones(N)        # Secondary diagonals: -1/dx^2
    dm1 = -alpha * np.ones(N)

    H = sparse.diags([dm1, d0, d1], offsets=[-1, 0, 1], shape=(N, N), format='csc')

    I = sparse.eye(N, format='csc')
    coef = (1j * dt) / 2.0
    M_L = I + coef * H
    M_R = I - coef * H

    solver = spla.factorized(M_L)
    return solver, M_R


def propagate(psi: np.ndarray, solver, M_R, steps: int, snap_every: int = 20):
    """Advance the packet ``steps`` times, recording density snapshots.

    Returns ``(psi_final, density_history)``.
    """
    density_history = []
    for step in range(steps):
        if step % snap_every == 0:
            density_history.append(np.abs(psi) ** 2)
        psi = solver(M_R.dot(psi))     # solve M_L psi^{n+1} = M_R psi^n
    density_history.append(np.abs(psi) ** 2)   # final state
    return psi, density_history


def probability_norm(psi: np.ndarray, dx: float) -> float:
    """Total probability integral of |psi|^2 (should stay 1 under unitary evolution)."""
    return float(np.sum(np.abs(psi) ** 2) * dx)


def transmission_probability(psi: np.ndarray, x: np.ndarray, dx: float,
                             x_min: float = 1.0) -> float:
    """Probability beyond the barrier (x > x_min) — the tunneled fraction."""
    return float(np.sum(np.abs(psi[x > x_min]) ** 2) * dx)


def reflection_probability(psi: np.ndarray, x: np.ndarray, dx: float,
                           x_max: float = 0.5) -> float:
    """Probability before the barrier (x < x_max) — the reflected fraction."""
    return float(np.sum(np.abs(psi[x < x_max]) ** 2) * dx)
