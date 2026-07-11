# Data — Multilingual Amazon Reviews Corpus

## Source

**Multilingual Amazon Reviews Corpus (MARC)**
- Publisher: Amazon (Keung et al., 2020)
- HuggingFace Hub: `mteb/amazon_reviews_multi`
- Paper: "The Multilingual Amazon Reviews Corpus" (EMNLP 2020)
- Languages: English (en), German (de), Spanish (es), French (fr), Japanese (ja), Chinese (zh)
- License: Released by Amazon for research purposes. See the dataset card on HuggingFace
  for the full license terms.

## Contents

Neither the sample nor the full corpus ships in this repo: the Amazon MARC license
restricts redistribution of the review text. Both are regenerated locally on demand and
are gitignored.

- `sample/` — A small stratified sample (~1,000 rows per language). Regenerate with
  `scripts/download_data.py --sample-only` (a few seconds).
- `full/` — The full dataset (~200k+ reviews per language). Regenerate with
  `scripts/download_data.py`.

## Star-to-sentiment mapping

| Stars | Sentiment | Rationale |
|---|---|---|
| 1–2 | Negative | Clear dissatisfaction |
| 3 | Neutral | Ambiguous; neither clearly positive nor negative |
| 4–5 | Positive | Clear satisfaction |

This 3-class mapping is a deliberate design choice: it creates a harder, more realistic
task than binary (positive/negative only) and avoids the noise of treating each star as
a separate class. The neutral class is the most challenging for any classifier.

## Integrity

- No data from the NDA-protected sentiment work enters this project.
- The sample is a deterministic stratified subset (seed=42) of the public corpus.
- The full dataset can be regenerated from scratch at any time.
