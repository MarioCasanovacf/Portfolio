# Data

## Files

### `kojeve_initial_agents.csv`
Stochastic population of 1,000 agents for the Kojève evolutionary game-theory
simulation. Each agent has traits drawn from Beta distributions modeling
asymmetric populations (most agents fear death more than they desire
recognition).

| Column | Type | Description |
|--------|------|-------------|
| Agent_ID | int | Unique agent identifier (0–999) |
| Fear_of_Death | float | Fear-of-death parameter, Beta(5, 2) distribution, range [0, 1] |
| Desire_for_Recognition | float | Desire-for-recognition parameter, Beta(2, 5) distribution, range [0, 1] |

### `hegel_phenomenology_corpus.txt`
Synthetic plain-text corpus representing Hegelian phenomenology and the
dialectical movement of Aufhebung (sublation). Contains dense philosophical
prose referencing key concepts: Being, Nothing, Becoming, Master, Slave,
Labor, Lordship, Self-Consciousness, Reason, and Spirit. Used as input for
knowledge-graph construction and eigenvector centrality analysis.

## Regeneration

To regenerate the data files, run from the project root:

```bash
python src/data_generator.py
```

Both files are generated deterministically with `np.random.seed(42)`.
