# 04 — Bioinformatics: Structural Biology as a Data Problem

**Domain:** Computational structural biology (in silico)
**Status:** In development — Ramachandran analysis complete, AlphaFold analysis coming

---

## Core Thesis

> Operating a physical laboratory for protein synthesis requires controlled reagents, extraction hoods, and specialized equipment. Approaching biomolecules as a problem of spatial topology and data analysis eliminates that barrier entirely, applying data science vectors to complex three-dimensional structures.
>
> A protein is not a biological mystery — it is a polymer whose behavior is fully determined by its three-dimensional conformation, which is in turn determined by geometrically constrained rotations of its atomic backbone. This is a linear algebra problem.

---

## Planned Projects

### Project A — Ramachandran Plot from Scratch *(complete)*
**File:** `ramachandran_plot_from_scratch.ipynb`

Calculates the φ (phi) and ψ (psi) backbone dihedral angles for every amino acid residue in a protein directly from atomic coordinates — without using any biochemistry library shortcuts. Pure vector mathematics: cross products, dot products, and atan2.

**What the Ramachandran plot shows:** A 2D scatter of (φ, ψ) pairs for all residues in a protein. High-density clusters correspond to secondary structure elements (α-helices and β-sheets). Empty regions correspond to sterically forbidden conformations — geometrically impossible because atomic radii would overlap.

**Mathematical core:**
```
Given 4 atoms A-B-C-D:
  b₁ = B - A,  b₂ = C - B,  b₃ = D - C
  n₁ = b₁ × b₂   (normal to plane of first three atoms)
  n₂ = b₂ × b₃   (normal to plane of last three atoms)
  φ  = atan2(|b₂| · b₁ · n₂,  n₁ · n₂)

For phi (φ): atoms C(i-1) → N(i) → Cα(i) → C(i)
For psi (ψ): atoms N(i)   → Cα(i) → C(i) → N(i+1)
```

### Project B — AlphaFold Structure Analysis
Dissection of protein structure predictions from AlphaFold2, parsing `.pdb` output files to:
- Calculate spatial distance matrices between amino acid side chains
- Identify zones of high density, hydrogen bond networks, and active sites
- Transform a biochemically opaque phenomenon into a navigable geometric model

### Project C — Isoelectric Precipitation Simulation
Computational simulation of the isoelectric precipitation process (the same physics that separates casein from milk when acid is added): modeling protein charge as a function of pH and predicting aggregation thresholds from pKa values of ionizable groups.

---

## Why This Section Exists in a Data Analytics Portfolio

Because the tools are the same. Parsing a `.pdb` file is a structured data extraction problem. Calculating dihedral angles is linear algebra. Identifying α-helix clusters in a Ramachandran plot is a density estimation problem solved with `scipy.stats.gaussian_kde`. Predicting protein aggregation from pH curves is regression.

The molecular biology is just the domain vocabulary. The mathematics is the same as everywhere else in this portfolio.

---

## Data Sources

- **Protein structures:** RCSB Protein Data Bank (rcsb.org) — public, free
- **AlphaFold predictions:** EBI AlphaFold Database — public, free
- **Protein sequences:** UniProt — public, free

All notebooks download data programmatically at runtime from public repositories.

## Requirements

```bash
pip install biopython numpy matplotlib scipy
```
