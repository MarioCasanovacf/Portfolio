# Where this data comes from, and how to check me

Two datasets live here, and they play different roles. `real/kc_house_data.csv` is the market —
the only file any conclusion about King County house prices is allowed to rest on. `synthetic/kc_house_data_synthetic.csv`
is an instrument check — a dataset where I planted the answer myself, kept only to prove the
pipeline can recover a *known* signal when one exists. Neither file is interchangeable with the
other, and the notebook is explicit every time it switches between them.

## `real/kc_house_data.csv` — the market

21,613 King County, WA residential sales, 21 columns, covering **2014-05-02 to 2015-05-27**.
This is the file everyone calls "the King County housing dataset" — originally assembled by
Kaggle user `harlfoxem` (`harlfoxem/housesalesprediction`, CC0: Public Domain) from King County
public-records sale data, and mirrored since on dozens of course repositories because Kaggle
itself needs an authenticated API key to fetch programmatically and this environment has none.

**Acquisition path and provenance check.** I could not use the Kaggle API (no credentials in
this environment, and installing one wasn't an option). Instead I pulled the file from two
independent, unrelated public GitHub mirrors and diffed them byte-for-byte before trusting
either:

- `https://raw.githubusercontent.com/ChengLi9/kc_house_data/master/kc_house_data.csv`
- `https://raw.githubusercontent.com/AbdulrahmenSalem/kc_house_data/main/kc_house_data.csv`

Both downloads are 2,515,206 bytes and hash identically:

```
sha256  d0875baa0251b21d4bdc9d2ae940a4fe0bb6009824f23dd0e2a5b2bf04557b7e   kc_house_data.csv
```

Two accounts with no visible relationship to each other, on two different default branches,
producing the exact same bytes, is the strongest provenance signal available without a Kaggle
login — it means neither is a one-off edited copy. The row count (21,613), column set, the
famous `bedrooms=33` data-entry error (see below), and the 2014–2015 date window all match the
dataset's well-known public description, which is the second independent check. If Mario later
gets Kaggle credentials, re-pulling `harlfoxem/housesalesprediction` and re-hashing against the
value above is the way to confirm this mirror was never tampered with.

**Known gotchas — read before trusting a number:**

- **`bedrooms = 33`, one row (`id=2402100895`)**, on a 1,620 sqft house with 1.75 bathrooms — a
  bedroom count that dense is not a real floor plan, it's a transcription error (almost
  certainly a `3` with an extra `3` typed). I flag rather than silently drop it: the notebook's
  `pipeline` section treats it as a declared robustness case, not a value to quietly delete
  before anyone can check my work.
- **`sqft_lot` has a long right tail** (rural/waterfront parcels several orders of magnitude
  larger than a city lot) — a lognormal-appropriate variable, not a normal one; treated that way
  in feature engineering.
- **177 `id` values repeat.** These are the same house sold twice within the 13-month window —
  legitimate re-sales, not duplicate rows to deduplicate. Any fold-safe grouping (the zipcode
  blocking in §4) should be aware that a repeat sale of the *same physical house* could still
  land in different folds, since the grouping key here is `zipcode`, not `id`. I did not
  additionally block on `id` — the ~0.8% of rows affected does not change the CV picture, but I
  say so instead of leaving it implicit.
- **No missing values.** Zero `NaN` across all 21 columns in this vintage of the file. That is
  worth stating plainly because the *synthetic* file below has injected NaNs and the pipeline is
  still built with an imputer inside it — defensively, not because this particular file needs
  one. If a future refresh of the source data reintroduces missingness, the pipeline does not
  silently break.
- **Prices are not inflation-adjusted** and the window is 13 months in 2014–2015 — eleven years
  stale as of this write-up. Nothing here should be read as a claim about 2026 King County
  prices; §7 of the notebook says this again in context.
- **70 zip codes**, 0.75% waterfront, no `Unnamed: 0` index column (that column exists only in
  the synthetic file below, which imitates a raw-CSV-export convention the real file does not
  have).

**License.** CC0 (public domain dedication), consistent with its origin in county public
records, which are themselves public information.

## `synthetic/kc_house_data_synthetic.csv` — the declared benchmark, not evidence about the market

5,000 fabricated rows produced by `src/data_generator.py`, seed 42. This file predates the
real-data acquisition above and used to be presented, uncritically, as if it *were* the King
County market. It is not, and it never told anyone anything true about King County — the
generator plants a price surface and the model comparison then "discovers" exactly what was
planted, which is a tautology, not a finding. It survives in this project for exactly one
purpose: to prove the analysis pipeline can recover a *known* signal, with the generating
parameters stated in full so nobody mistakes recovery-of-a-plant for discovery-of-a-market.

**Every parameter that manufactures `price`, stated plainly:**

```
n_houses = 5,000, seed = 42

base_price = sqft_living * 150
           + (grade - 7) * 50,000
           + sqft_living * (grade - 7) * 12      # planted interaction term
           + (condition - 3) * 20,000
           + waterfront * 300,000
           + view * 25,000
           + spatial_premium                      # planted, NON-additive in lat/long

spatial_premium = sum over 3 Gaussian "hotspots" of amp * exp(-((lat-lat_c)^2 + (long-long_c)^2) / 0.012):
    hotspot 1: (lat=47.62, long=-122.21), amplitude $220,000   # Bellevue/Medina/Mercer Island
    hotspot 2: (lat=47.63, long=-122.35), amplitude $150,000   # Seattle core / downtown waterfront
    hotspot 3: (lat=47.57, long=-122.04), amplitude  $90,000   # Sammamish plateau

price = clip(base_price * lognormal(mean=0, sigma=0.25), 75_000, 5_000_000)

NaN injection: bedrooms ~2.5% missing (random), bathrooms ~2.0% missing (random)
```

The three hotspot amplitudes and the `sigma²=0.012` decay width are the whole ballgame: they set
exactly how much R² a model that can represent non-additive spatial structure (a tree ensemble)
should pick up over one that cannot (an additive linear model). The notebook's benchmark section
computes that gap on this file — call it ΔR²_synthetic — as a positive control, then computes
the analogous gap on the *real* file — ΔR²_real — and compares the two. If ΔR²_real is much
smaller than ΔR²_synthetic, King County's real spatial structure is weaker than what I planted
here; if it's comparable, the real market really does have hotspot-like non-additive geography.
Either answer is legitimate; neither was baked in by this file, because this file only supplies
the positive-control side of that comparison.

**Regenerating it** (deterministic, same seed 42 every time):

```bash
python src/data_generator.py
```

writes to `data/synthetic/kc_house_data_synthetic.csv`, relative to the project root regardless
of the working directory the script is invoked from (the previous default wrote to `../data`,
which escaped the project when run from anywhere but `src/` — fixed, see `src/data_generator.py`).
