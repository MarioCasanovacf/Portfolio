import os

import numpy as np
import pandas as pd

# Determinism for scientific reproducibility
np.random.seed(42)


def generate_rutherford_ensemble(output_dir="data", n_particles=5000):
    """
    Bulk initialization routine.
    Generates a Monte Carlo ensemble of alpha particles (He2+) that will be
    fired at a target nucleus (gold, Au), assigning initial position vectors
    and stochastic momentum.
    """
    os.makedirs(output_dir, exist_ok=True)
    particles_path = os.path.join(output_dir, "rutherford_initial_particles.csv")

    # Basic physical parameters in simplified atomic units.
    # Initial position: far along the negative X axis.
    x_initial = np.full(n_particles, -500.0)

    # Impact parameter (b) distributed stochastically along Y,
    # simulating a uniform cylindrical beam.
    y_initial = np.random.uniform(-50.0, 50.0, n_particles)
    z_initial = np.random.uniform(-50.0, 50.0, n_particles)

    # Initial momentum (positive X direction only) with a small thermal spread.
    vx_initial = np.random.normal(10.0, 0.1, n_particles)
    vy_initial = np.zeros(n_particles)
    vz_initial = np.zeros(n_particles)

    df_ensemble = pd.DataFrame(
        {
            "Particle_ID": np.arange(n_particles),
            "x": x_initial,
            "y": y_initial,
            "z": z_initial,
            "vx": vx_initial,
            "vy": vy_initial,
            "vz": vz_initial,
            "charge_q1": 2.0,  # alpha particle (+2e)
            "mass_m1": 4.0,  # approximate mass 4u
        }
    )

    df_ensemble.to_csv(particles_path, index=False)
    print(
        f"[+] Monte Carlo ensemble ({n_particles} alpha particles) generated at: {particles_path}"
    )


def generate_quantum_potential_barrier(output_dir="data"):
    """
    Define the parameters of a 1D potential barrier for the time-dependent
    Schrödinger equation. This file dictates the topology of the spatial
    grid V(x).
    """
    os.makedirs(output_dir, exist_ok=True)
    barrier_path = os.path.join(output_dir, "quantum_barrier_profile.csv")

    # 1D grid from -5 to 5
    x = np.linspace(-5, 5, 1000)
    V = np.zeros_like(x)

    # Square barrier between x=0.5 and x=1.0 with height V0
    V0 = 50.0
    barrier_mask = (x >= 0.5) & (x <= 1.0)
    V[barrier_mask] = V0

    df_barrier = pd.DataFrame({"x": x, "V": V})
    df_barrier.to_csv(barrier_path, index=False)
    print(f"[+] Quantum potential profile generated at: {barrier_path}")


if __name__ == "__main__":
    print("[*] Initializing boundary conditions and physical ensembles...")
    generate_rutherford_ensemble()
    generate_quantum_potential_barrier()
