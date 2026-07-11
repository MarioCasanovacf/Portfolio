// Catalogue of case studies. Two audiences, split by `track`:
//   'industry'     — applied / hireable engineering → the "Case Studies" page (home)
//   'intellectual' — conceptual experiments          → the "Experiments" page
//
// Order matters — the number shown in each index is derived from position here,
// not stored. Companions (interactive islands) inherit the prior number's slot.
//
// `published: true`  → the MDX page exists and the row is a live link.
// `published` unset  → the study is not yet reviewed by Mario; the row renders as
//                      "Coming soon" with its domain, dek and methods hidden.
//                      Flip to true (and create the MDX) once it has been edited.
// `published: import.meta.env.DEV`
//                    → pending Mario's approval: visible and readable on the
//                      local dev server (`npm run dev`), hidden in any built /
//                      published output. CaseStudyLayout also gates the route
//                      itself, so the page is unreachable by direct URL in prod.

export type Track = 'industry' | 'intellectual';

export interface Study {
  slug: string;
  track: Track;
  domain: string;
  title: string;
  dek: string;
  methods: string[];
  /** Whether the reviewed MDX page exists. Unpublished rows render as
   *  "Coming soon" and are not clickable. */
  published?: boolean;
  /** A companion tool (e.g. an interactive island), not a standalone case study.
   *  Listed in the index but not counted or numbered as one of the case studies. */
  companion?: boolean;
}

export const studies: Study[] = [
  // ── Industry · applied → "Case Studies" ─────────────────────────────────────
  {
    slug: 'agent-harness',
    track: 'industry',
    domain: 'Agent orchestration',
    title: 'A multi-agent, multi-layer and auto-evolving harness for the era after Fable 5: Building a functional society of agents to enhance AI workflows.',
    dek: 'A file-based coordination substrate designed to orchestrate a society of cheaper models (Sonnet) under a single frontier coordinator (Opus), routing routine work to cheaper tiers while reserving the coordinator for high-stakes decisions. Running on a 22-task board (18 done, 2 failed, 2 open), it enforces a mechanical producer≠approver gate and TTL write-locks. The harness evolved across four generations of self-audits, generating 25 accepted mutations. The honest limits—the lack of a wall-clock control run, the unmeasured token-shift, and reporting the evolution history as provenance—are the load-bearing core.',
    methods: ['Shared blackboard (task DAG)', 'TTL write-locks', 'Producer ≠ approver', 'Evidence replay'],
    published: true,
  },
  {
    slug: 'sentiment-cascade',
    track: 'industry',
    domain: 'Applied machine learning',
    title: 'The labels are the product',
    dek: 'Two production sentiment models for a consumer smart-home hardware company — companion-app reviews across more than 20 languages, a large corpus of retailer product reviews — built on the premise that the fine-tuned transformer is the commodity and the label standard is the asset: rubrics versioned under blind Cohen-κ audits (0.472 → 0.688 the hard way, 0.915 before a single label the disciplined way), cascade routing chosen by a measured F1 = 0.000 failure, and a rival brand’s name caught carrying a 1.52× negativity lift — an unintentional leak, masked before training.',
    methods: ['Labeling rubric + κ audits', 'XLM-RoBERTa cascades', 'Threshold calibration', 'Leakage control'],
    published: true,
  },
  {
    slug: 'cloud-ops',
    track: 'industry',
    domain: 'Cloud infrastructure',
    title: "Operating on clouds you can't control",
    dek: 'Five operational questions answered on 787 real incidents from 18 provider status pages and 700 real CI runs: what SLO you can honestly promise, which number to staff with, how many engineers the worst week needs, whether minute-zero prediction works (it doesn’t), and what to triage when the outage isn’t yours.',
    methods: ['Error budgets', 'Log-normal TTR', 'Erlang C · Allen-Cunneen', 'cμ-rule triage'],
    published: true,
  },
  {
    slug: 'staffing-calculator',
    track: 'industry',
    domain: 'Cloud infrastructure',
    title: 'Interactive — the team the textbook recommends',
    dek: 'A live companion to the study above: set how fast incidents arrive and how long a fix takes, then flip one switch (from a world where every fix looks alike to the one this capture measured) and watch the honest headcount move from two engineers to three with nothing else touched.',
    methods: ['React island', 'Erlang C · Allen–Cunneen', '36-incident week', '2 → 3 engineers'],
    published: true,
    companion: true,
  },
  {
    slug: 'local-vs-frontier',
    track: 'industry',
    domain: 'Applied machine learning',
    title: 'The model you keep',
    dek: 'A comparative benchmark of a locally fine-tuned DistilBERT classifier against frontier APIs like Claude 4.8 and GPT-5.5. Measures a throughput of 237 reviews/second on MPS local GPU, and maps the economic break-even point against DeepSeek\'s $0.14/1M commodity pricing.',
    methods: ['Transformers', 'Inference Throughput', 'MPS Acceleration', 'Inference Cost Modeling'],
    // The notebook folder is public (Amazon MARC corpus, redistributable; full
    // data + model weights gitignored as regenerable, code + sample committed).
    published: true,
  },
  {
    slug: 'legislative-pipeline',
    track: 'industry',
    domain: 'Legislative data engineering',
    title: 'Representative democracy in Mexico: data a server will render but no one will hand you',
    dek: 'Per-deputy roll-call votes scraped from government HTML and an academic corpus, conformed into one dated-history star across three legislatures. 798k votes attributed as-of their date — an independent count that reproduces the official tallies on all 274 recent votes — and a caucus-switch signal that honestly deflates from 82 to 15 once coalition label-noise is stripped.',
    methods: ['Web scraping', 'dbt + DuckDB', 'SCD Type 2 (as-of join)', 'Gaps-and-islands'],
    published: true,
  },
  {
    slug: 'legislative-explorer',
    track: 'industry',
    domain: 'Legislative data engineering',
    title: 'Interactive — the LXVI roll-call, vote by vote',
    dek: 'A live companion to the pipeline above: pick any of the 274 recorded votes and see how each party — and each of the 554 deputies — voted, reconciled to the chamber’s own official tallies.',
    methods: ['React island', 'DuckDB export', '274 votes', '554 deputies'],
    published: true,
    companion: true,
  },
  {
    slug: 'hierarchical-risk-parity',
    track: 'industry',
    domain: 'Quantitative finance',
    title: 'Hierarchical Risk Parity, or: how to allocate without inverting a covariance matrix',
    dek: 'Replaces the unstable Markowitz inversion with hierarchical clustering of the correlation matrix and recursive bisection along the resulting tree. No matrix is ever inverted; weights vary continuously with the inputs.',
    methods: ['Ward linkage', 'Quasi-diagonalisation', 'Recursive bisection', 'IVP'],
  },
  {
    slug: 'heston',
    track: 'industry',
    domain: 'Quantitative finance',
    title: 'Exotic options under stochastic volatility, and what antithetic variates actually buy',
    dek: 'A path-dependent Asian call under Heston stochastic volatility has no closed form, so 50,000-path Monte Carlo is the only real option — and antithetic variates promise a cheaper one. Measured rather than assumed: paired against plain Monte Carlo at the same path budget, the antithetic estimator lands at $5.2019 (±$0.0186) against $5.2516 (±$0.0294), roughly a 1.6× tighter standard error from one seed, driven by a −0.598 correlation between each path and its mirror. Inputs are illustrative, not calibrated to any market.',
    methods: ['Heston model', 'Euler–Maruyama', 'Antithetic variates', 'Monte Carlo'],
    published: import.meta.env.DEV,
  },
  {
    slug: 'us-housing-archetypes',
    track: 'industry',
    domain: 'Real estate analytics',
    title: 'US housing market archetypes: systematic classification of affordability and volatility through three cycles',
    dek: 'A systematic classification of 30 metropolitan housing markets on affordability and price volatility from 2000 to 2026. Identifies three data-driven archetypes (A = SF/Seattle, B = Houston, C = DC) and tests homeownership accessibility across local county-level income boundaries. Explores temporal dynamics under GFC, COVID, and post-2022 rate shocks, revealing that affordability and cyclical stability are decoupled dimensions. Validates spatial-signal persistence on King County housing sales vs. memoized target-encoding baseline.',
    methods: ['Systematic Ranking (NAR HAI)', 'Augmented Dickey-Fuller & Ljung-Box', 'Block Bootstrap', 'Target Encoding Baseline'],
    published: import.meta.env.DEV,
  },

  // ── Intellectual · play → "Experiments" ─────────────────────────────────────
  {
    slug: 'legislative-experiments',
    track: 'intellectual',
    domain: 'Computational politics',
    title: 'Five hypotheses about a one-party chamber',
    dek: 'Exploratory tests on the LXVI roll-call: the two blocs actually agree 57% of the time, absence is used to skip routine votes (not dodge contentious ones), floor leaders track their caucus to ≥99.6%, and the only deputies who cross the aisle are all from MC — including, at the same rate, MC’s own floor coordinator.',
    methods: ['DuckDB + pandas', 'Roll-call analysis', 'Jupyter'],
    published: true,
  },
  {
    slug: 'ramachandran',
    track: 'intellectual',
    domain: 'Structural biology',
    title: 'Ramachandran topology from atomic coordinates',
    dek: 'Dihedral φ and ψ angles computed from scratch using vector geometry over PDB-sourced atomic coordinates. The plot reveals alpha-helix and beta-sheet basins as data, not as illustration.',
    methods: ['Vector geometry', 'PDB parsing'],
  },
  {
    slug: 'symplectic-integration',
    track: 'intellectual',
    domain: 'Computational physics',
    title: 'Symplectic integration of bound orbits',
    dek: 'A two-body Kepler problem under Forward-Euler, RK4, Velocity-Verlet, and Yoshida 4. The argument that conserved energy is the wrong invariant, and the geometry that says so.',
    methods: ['Velocity-Verlet', 'Yoshida 4', 'Symplectic geometry'],
  },
  {
    slug: 'kojeve',
    track: 'intellectual',
    domain: 'Continental philosophy',
    title: 'Kojevian dialectics as evolutionary game theory',
    dek: 'A thousand agents play recognition games with asymmetric payoffs. Master-slave inequality emerges, then dissolves through Aufhebung — giving Kojève’s end-of-history thesis a precise, reproducible mechanism.',
    methods: ['Agent-based modelling', 'Stochastic payoffs', 'Eigenvector centrality'],
  },
  {
    slug: 'fiscal',
    track: 'intellectual',
    domain: 'Macroeconomic capture',
    title: 'Fiscal crowding-out as a budget constraint',
    dek: 'Schumpeterian friction between deficit financing and private capital formation, traced through the long-run correlation between sovereign issuance and corporate borrowing rates.',
    methods: ['Time series', 'Pearson correlation'],
  },
];

/** Studies for one subsection, in declared order. */
export const studiesByTrack = (track: Track): Study[] =>
  studies.filter((s) => s.track === track);
