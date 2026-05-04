# ADR 002 — Modular package layout vs flat layout

**Status:** Accepted
**Date:** 2026-04-20

## Context

The original repository had a single flat module `src/data_generator.py` with
two top-level functions and notebooks invoking them via relative paths. This
worked for exploratory work but blocks:

- Installable distribution (`pip install -e .`).
- IDE refactoring across files.
- Importable from `tests/` without `sys.path` hacks.
- Future expansion (HRP, Heston, LOB modules each with their own tests).

## Options considered

1. **Keep flat** — minimal change, append new functions to `data_generator.py`
   and add neighbours like `hrp.py`, `heston.py`.
2. **Single-package, src layout** — move code to `src/quantitative_finance/`,
   subdivide by domain (`data/`, `models/`, `utils/`, `reports/`).
3. **Namespace package** — multiple packages under a parent namespace
   (`qf.data`, `qf.models`). Useful at scale but overkill for 3 workloads.

## Decision

Adopt option **2 (single-package, src layout)** following the convention
established by `legislative-data-pipeline` and codified in
[PRODUCTION_TEMPLATE.md](../../../PRODUCTION_TEMPLATE.md) section 1.

Rationale:
- `src/` layout forces `pip install -e .` so imports always go through the
  installed package — no accidental path resolution.
- Subdividing by domain (`data`, `models`, `utils`, `reports`) keeps each module
  focused; tests mirror the structure 1:1.
- The CLI lives at the package root (`cli.py`), invoked via `[project.scripts]`.

## Consequences

**Positive**
- Clean imports: `from quantitative_finance.data.generator import generate_lob_events`.
- Tests run without `PYTHONPATH` tricks.
- Adding `models/hrp.py`, `models/heston.py`, `models/lob_microstructure.py` is
  a localized change.

**Negative**
- Existing notebooks that imported from `data_generator` (none observed) would
  need updating to `from quantitative_finance.data.generator import …`.
- Slight learning curve for contributors unfamiliar with the `src/` convention.
