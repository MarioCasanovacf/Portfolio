import os
import pandas as pd
import numpy as np

# Determinismo para reproducibilidad científica
np.random.seed(42)

def generate_rutherford_ensemble(output_dir="../data", n_particles=5000):
    """
    Rutina de inicialización masiva.
    Genera un ensamble de Monte Carlo de partículas alfa (He2+) que serán
    disparadas hacia un núcleo objetivo (Oro - Au), asignando
    vectores de posición inicial y momento estocástico.
    """
    os.makedirs(output_dir, exist_ok=True)
    particles_path = os.path.join(output_dir, "rutherford_initial_particles.csv")
    
    # Parámetros físicos básicos en unidades atómicas simplificadas
    # Posición inicial: Lejos en el eje X negativo
    x_initial = np.full(n_particles, -500.0)
    
    # Parámetro de impacto (b) distribuido estocásticamente en el eje Y
    # Simulando un haz uniforme cilíndrico
    y_initial = np.random.uniform(-50.0, 50.0, n_particles)
    z_initial = np.random.uniform(-50.0, 50.0, n_particles)
    
    # Momento inicial (solo en dirección X positiva) con ligera dispersión térmica
    vx_initial = np.random.normal(10.0, 0.1, n_particles)
    vy_initial = np.zeros(n_particles)
    vz_initial = np.zeros(n_particles)
    
    df_ensemble = pd.DataFrame({
        'Particle_ID': np.arange(n_particles),
        'x': x_initial,
        'y': y_initial,
        'z': z_initial,
        'vx': vx_initial,
        'vy': vy_initial,
        'vz': vz_initial,
        'charge_q1': 2.0,   # Partícula alfa (+2e)
        'mass_m1': 4.0      # Masa aproximada 4u
    })
    
    df_ensemble.to_csv(particles_path, index=False)
    print(f"[+] Ensamble Monte Carlo ({n_particles} partículas alfa) generado en: {particles_path}")

def generate_quantum_potential_barrier(output_dir="../data"):
    """
    Define los parámetros de una barrera de potencial 1D para la
    ecuación de Schrödinger dependiente del tiempo. Este archivo dictará
    la topología de la malla espacial V(x).
    """
    os.makedirs(output_dir, exist_ok=True)
    barrier_path = os.path.join(output_dir, "quantum_barrier_profile.csv")
    
    # Grid unidimensional de -5 a 5
    x = np.linspace(-5, 5, 1000)
    V = np.zeros_like(x)
    
    # Barrera cuadrada entre x=0.5 y x=1.0 de altura V0
    V0 = 50.0
    barrier_mask = (x >= 0.5) & (x <= 1.0)
    V[barrier_mask] = V0
    
    df_barrier = pd.DataFrame({'x': x, 'V': V})
    df_barrier.to_csv(barrier_path, index=False)
    print(f"[+] Perfil de Potencial Cuántico generado en: {barrier_path}")

if __name__ == "__main__":
    print("[*] Inicializando condiciones de frontera y ensambles físicos...")
    generate_rutherford_ensemble()
    generate_quantum_potential_barrier()
