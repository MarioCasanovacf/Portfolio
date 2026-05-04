# Data

## Files

### `rutherford_initial_particles.csv`
Monte Carlo ensemble of 5,000 alpha particles (He2+) with initial positions and momenta, used as input for Rutherford scattering simulation against a gold (Au) nucleus.

| Column | Type | Description |
|--------|------|-------------|
| Particle_ID | int | Unique particle identifier (0-4999) |
| x | float | Initial x position (fixed at -500.0, far from target) |
| y | float | Initial y position, uniform random in [-50, 50] (impact parameter) |
| z | float | Initial z position, uniform random in [-50, 50] |
| vx | float | Initial x-velocity, normal distribution centered at 10.0 |
| vy | float | Initial y-velocity (fixed at 0.0) |
| vz | float | Initial z-velocity (fixed at 0.0) |
| charge_q1 | float | Particle charge in elementary units (fixed at 2.0 for alpha particle) |
| mass_m1 | float | Particle mass in atomic mass units (fixed at 4.0) |

### `quantum_barrier_profile.csv`
One-dimensional potential barrier profile V(x) for time-dependent Schrodinger equation simulation. Defines a square barrier of height V0=50.0 between x=0.5 and x=1.0 on a 1,000-point grid.

| Column | Type | Description |
|--------|------|-------------|
| x | float | Spatial coordinate, linearly spaced from -5.0 to 5.0 |
| V | float | Potential energy at position x (0.0 outside barrier, 50.0 inside) |

## Regeneration

To regenerate the data files, run from the project root:

```bash
python src/data_generator.py
```

Both files are generated deterministically with `np.random.seed(42)`.
