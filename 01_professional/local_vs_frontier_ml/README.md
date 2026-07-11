# Local vs Frontier ML — When to Own a Model

A standalone, reproducible case study that benchmarks a locally fine-tuned multilingual
sentiment classifier (DistilBERT, `distilbert-base-multilingual-cased`) against frontier
LLM APIs on cost, throughput, determinism, and accuracy — and documents the deployment
pattern where each tool belongs.

## Thesis

> The frontier model is the tool you build the solution *with*, alongside the engineer.
> Its place is development (labeling, generating, adjudicating — under audit), and the
> artifact that ships is a small, owned, local model. Knowing how to divide those two
> jobs is what this case study documents, and the pattern extends well beyond sentiment —
> its purpose is Applied Machine Learning to Business.

## Data

**Multilingual Amazon Reviews Corpus** (public, redistributable, multilingual).
Six languages: English, German, Spanish, French, Japanese, Chinese.
Stars mapped to 3-class sentiment: negative (1–2), neutral (3), positive (4–5).

A small sample is committed in `data/sample/`. To regenerate the full dataset:

```bash
../../.venv/bin/python scripts/download_data.py
```

## Reproduction

```bash
cd notebooks/
../../../.venv/bin/jupyter nbconvert --execute --inplace \
  --ExecutePreprocessor.timeout=3600 \
  01_local_vs_frontier_benchmark.ipynb
```

Requires the portfolio shared venv (`Portfolio-repo/.venv`) with `torch`, `transformers`,
and `datasets` installed.

## Structure

```
local_vs_frontier_ml/
├── README.md                  # This file
├── research/
│   └── design_modelos_pequenos_vs_frontier.md   # Design doc (Spanish)
│   └── frontier_sources.md    # Cited frontier benchmarks with URLs and dates
├── notebooks/
│   └── 01_local_vs_frontier_benchmark.ipynb     # The deliverable
├── data/
│   ├── README.md              # Data provenance and license
│   └── sample/                # Small committed sample (~1k rows)
└── scripts/
    └── download_data.py       # Full dataset download/regeneration
```

## Connection to the portfolio

This is the second applied-ML case study (slot `ml-second` in the site). The sentiment
work that motivated this pattern is cited as the real-world case but remains private
(NDA); nothing from that project is imported here. This project is 100% public and
reproducible.

## License

Data: Multilingual Amazon Reviews Corpus is released under a research-friendly license
by Amazon (see `data/README.md` for details).
Code: Same license as the portfolio repository.
