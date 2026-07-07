import os

import numpy as np
import pandas as pd

# Historical determinism
np.random.seed(42)


def generate_hegelian_corpus(output_dir="data"):
    """
    Generate a synthetic plain-text corpus representing Hegelian phenomenology
    and the dialectical movement of Aufhebung (sublation).
    """
    os.makedirs(output_dir, exist_ok=True)
    corpus_path = os.path.join(output_dir, "hegel_phenomenology_corpus.txt")

    # Highly dense synthetic text designed to stress-test nodal centrality
    text = (
        "Being in itself is pure and indeterminate, but in its immediacy it inevitably "
        "transitions toward Nothing. This immediacy of Being and Nothing finds its truth "
        "in Becoming. "
        "Likewise, the Master risks his life for recognition, establishing the paradigm "
        "of Lordship. The Slave flees from death and embraces Labor, transforming "
        "objective Nature. The Slave's Labor transcends the Master's stagnant Lordship. "
        "Through Aufhebung, Labor and Lordship converge into absolute Self-Consciousness. "
        "Reason surpasses subjective Self-Consciousness to reach Spirit."
    )

    with open(corpus_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[+] Hegelian corpus generated successfully at: {corpus_path}")


def generate_kojeve_agents(output_dir="data", n_agents=1000):
    """
    Generate an initial stochastic population of historical agents for the
    Kojève evolutionary game-theory simulation. Assigns distributions over
    'Desire for Recognition' and 'Fear of Death'.
    """
    os.makedirs(output_dir, exist_ok=True)
    agents_path = os.path.join(output_dir, "kojeve_initial_agents.csv")

    # Beta distribution to simulate asymmetric populations.
    # Most agents fear death more than they desire recognition: beta(5, 2).
    fear_of_death = np.random.beta(5, 2, n_agents)

    # Desire for recognition skewed in the opposite direction (alpha < beta).
    desire_for_recognition = np.random.beta(2, 5, n_agents)

    # Columns are written in Spanish (the data's native language); the notebook normalises
    # them to English (Fear_of_Death, Desire_for_Recognition) at load time.
    df_agents = pd.DataFrame(
        {
            "Agent_ID": np.arange(n_agents),
            "Miedo_a_la_Muerte": fear_of_death,
            "Deseo_de_Reconocimiento": desire_for_recognition,
        }
    )

    df_agents.to_csv(agents_path, index=False)
    print(
        f"[+] Kojève multi-agent environment ({n_agents} agents) initialized at: {agents_path}"
    )


if __name__ == "__main__":
    print("[*] Generating pre-analytical data structures...")
    generate_hegelian_corpus()
    generate_kojeve_agents()
