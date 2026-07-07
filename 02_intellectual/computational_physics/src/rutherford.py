"""Velocity-Verlet integration of Coulomb (Rutherford) scattering.

A symplectic Velocity-Verlet integrator pushes charged particles past a fixed
nucleus; the asymptotic deflection reproduces Rutherford's law
``tan(theta/2) = a / b`` with Coulomb length ``a = k_e q1 Q / (m v0^2)``, from which
the differential cross section ``dsigma/dOmega ∝ csc^4(theta/2)`` follows. The JIT
kernels here are imported by ``notebooks/01_Rutherford_Scattering_Simulation.ipynb``
so the simulation and the unit tests run the same integrator.
"""

from __future__ import annotations

import numpy as np
from numba import jit

# Physical constants naturalized to the simulated environment
k_e = 1.0    # Scaled Coulomb constant
Q_au = 79.0  # Gold charge (target nucleus)


@jit(nopython=True)
def compute_coulomb_force(x, y, q1_val, m1_val):
    """
    Vectorized computation of the inverse square of distance.
    F = (k_e * q1 * Q_au) / r^2 in radial direction.
    Returns accelerations ax, ay.
    """
    r_sq = x**2 + y**2
    # We prevent purely central collision divergences by adding a smoothing factor
    r_sq = np.where(r_sq < 1.0, 1.0, r_sq)
    r = np.sqrt(r_sq)

    force_mag = (k_e * q1_val * Q_au) / r_sq

    # Decomposition of the (repulsive) radial force vector
    ax = (force_mag / m1_val) * (x / r)
    ay = (force_mag / m1_val) * (y / r)

    return ax, ay


@jit(nopython=True)
def verlet_integrator(x, y, vx, vy, dt, steps, q1_val, m1_val):
    """
    Evolves the dynamic Hamiltonian system.
    We use Velocity-Verlet to not artificially drain thermal energy.
    """
    N = len(x)

    # Arrays to store trajectories of a subset (for trace plots)
    n_traces = 50
    x_trace = np.zeros((steps, n_traces))
    y_trace = np.zeros((steps, n_traces))

    # Initial acceleration conditions
    ax, ay = compute_coulomb_force(x, y, q1_val, m1_val)

    for t in range(steps):
        # 1. Update Position: r(t+dt) = r(t) + v(t)dt + 0.5*a(t)dt^2
        x_new = x + vx * dt + 0.5 * ax * dt**2
        y_new = y + vy * dt + 0.5 * ay * dt**2

        # 2. Compute New Acceleration a(t+dt)
        ax_new, ay_new = compute_coulomb_force(x_new, y_new, q1_val, m1_val)

        # 3. Update Velocity: v(t+dt) = v(t) + 0.5*(a(t) + a(t+dt))dt
        vx_new = vx + 0.5 * (ax + ax_new) * dt
        vy_new = vy + 0.5 * (ay + ay_new) * dt

        # Synchronous reassignment
        x, y = x_new, y_new
        vx, vy = vx_new, vy_new
        ax, ay = ax_new, ay_new

        # Store traces (first 50 particles)
        x_trace[t, :] = x[:n_traces]
        y_trace[t, :] = y[:n_traces]

    return x_trace, y_trace, vx, vy


def coulomb_length(q1: float, m1: float, v0: float) -> float:
    """Rutherford Coulomb length a, where tan(theta/2) = a / b."""
    return k_e * q1 * Q_au / (m1 * v0**2)


def scattering_angles_deg(vx: np.ndarray, vy: np.ndarray) -> np.ndarray:
    """Deflection angle (degrees) of each particle from the +x beam axis."""
    return np.degrees(np.arctan2(vy, vx))
