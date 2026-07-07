# Intellectual Testbed

> Experiments in making an argument **computable**. The value here is the argument, not the engineering — these are demonstrations of a thesis, not a job application.

This track exists because a quantified piece of philosophy, a numerically reproduced physical law, or a canonical result rebuilt from first principles is a strange thing to put in a *professional* portfolio: to a recruiter it reads as noise or pretension. But as a body of work tied to a blog, it's a brand asset — it shows how I think when I take a hard idea and refuse to hand-wave it.

So each project here is framed as a **hypothesis experiment**: a claim, a way of making the claim computable, and a result that either supports it or doesn't. The hireable engineering lives in the [professional track](../01_professional/); what lives here is the reasoning.

---

## `continental_philosophy/` — can a philosophical argument be made computable?

**Hypothesis:** the formal structure latent in continental philosophy can be rendered as graph topology and dynamical systems without flattening the argument.

- **`01_Dialectical_Knowledge_Graph`** — Hegelian *Aufhebung* encoded as hand-built semantic triplets, then read with eigenvector centrality: which concepts are load-bearing in the dialectic?
- **`02_Kojeve_Evolutionary_Game_Theory`** — Kojève's master/slave dialectic as an agent-based recognition network with a logistic decision rule, watched for percolation and entropy convergence.

**What it demonstrates:** that "recognition" and "supersession" can be operationalized as measurable structure — and where that operationalization starts to strain.

---

## `computational_physics/` — do the canonical results fall out of an honest numerical scheme?

**Hypothesis:** the textbook laws aren't inputs to fit; they emerge from a faithful first-principles simulation, and you can prove it by checking the invariants.

- **`01_Rutherford_Scattering`** — a velocity-Verlet Monte Carlo ensemble of α-particles under a Coulomb force (Numba-JIT). The differential cross-section is *recovered*, and a property test pins it to the **csc⁴(θ/2)** law by its log-log shape — not merely its monotonicity.
- **`02_Schrodinger_Crank_Nicolson`** — quantum tunneling through a barrier via a Crank-Nicolson solve on a tridiagonal sparse system. The scheme's **unitarity** is tested (norm ≡ 1), and transmission + reflection sum to one.

**What it demonstrates:** that the physics is correct *because the conserved quantities are conserved* — the tests check laws, not fitted numbers.

---

## `proteins_ramachandran_plot/` — is protein conformation just geometry?

**Hypothesis:** the allowed shapes of a protein backbone are a geometric fact computable from atomic coordinates alone — no specialised library required.

A from-scratch parser pulls backbone N/Cα/C atoms from a real PDB structure (1AHO, a scorpion neurotoxin); dihedral φ/ψ angles come from pure vector calculus (cross products + `atan2`); the Ramachandran allowed regions appear. A property test checks the dihedral math against hand-built geometries with known angles.

**What it demonstrates:** that the Ramachandran plot — usually produced by a black-box tool — is recoverable from first principles, and that the constraint is geometric, not empirical.

---

## `proteins_alphafold_distances/` — does 3D structure reduce to a distance object?

**Hypothesis:** a protein's spatial organisation can be captured as a single computable topology — the Cα–Cα distance matrix / contact map.

From the coordinates of Ubiquitin (1UBQ), a Euclidean distance matrix is built and read as a contact map. Property tests pin the matrix's defining invariants (symmetry, zero diagonal, the metric itself), and the parser is tested against an inline fixture so the column-slicing can't silently drift.

**What it demonstrates:** that "structure" can be reduced to a distance-geometry object you can compute, visualise, and reason about directly.

---

## `macroeconomic_capture/` — can a contested macro narrative be put to the data?

**Hypothesis:** the friction between public policy and private capital formation isn't only rhetorical — it can be operationalized and tested.

- **`01_Fiscal_Crowding_Out`** — the government budget constraint read as a time series: does public borrowing co-move with private investment the way the crowding-out story claims?
- **`02_Zombie_Corporations`** — a Schumpeterian survival question answered with DBSCAN, treating perpetually-unprofitable-but-alive firms as a topological anomaly.

**What it demonstrates:** that a Schumpeterian argument about capital and creative destruction can be made empirical, with the data allowed to push back.

---

## Conventions

Each project is independently installable and tested:

```bash
cd 02_intellectual/<project>
pip install -e ".[dev,notebooks]"
pytest -m unit
```

The computational logic lives in importable, unit-tested `src/` modules; the notebooks import it, so what you read in the analysis is the same code the property tests exercise.
