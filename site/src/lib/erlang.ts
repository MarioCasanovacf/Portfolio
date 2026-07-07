// The staffing math behind the interactive calculator, ported line for line
// from NB03 (Portfolio-repo/01_professional/cloud_infrastructure_support/
// notebooks/03_staffing_erlang.ipynb). The notebook is canonical; if the two
// ever disagree, the notebook wins and this file has a bug.
//
// Model: M/M/c queue (Erlang C, 1917) for the textbook reading, with the
// Allen–Cunneen heuristic — expected wait scaled by f = (c²ₐ + c²ₛ)/2 — for
// the reading that consumes the measured variability.

/** Parameters measured in the capture's peak week (2026-06-07 to 06-13). */
export const MEASURED = {
  /** Peak-week arrival rate: 36 declared incidents over 7 days ≈ 5.14/day. */
  lambdaPerDay: 5.14,
  /** Mean open duration in that window, minutes. */
  meanServiceMin: 156,
  /** Squared CV of arrivals (dispersion index of daily counts, NB03 cell 9). */
  ca2: 1.65,
  /** Squared CV of service times (NB03 cell 11). */
  cs2: 13.47,
  /** Service-level threshold: an incident should not wait longer than this. */
  thresholdMin: 30,
  /** Target: at most this fraction of incidents waits past the threshold. */
  target: 0.1,
} as const;

/** Textbook world: Poisson arrivals, exponential service → c²ₐ = c²ₛ = 1. */
export const F_TEXTBOOK = 1;

/** Measured world: f = (c²ₐ + c²ₛ)/2 = (1.65 + 13.47)/2 = 7.56. */
export const F_MEASURED = (MEASURED.ca2 + MEASURED.cs2) / 2;

/** Offered load in erlangs: arrivals per minute × mean service minutes. */
export function offeredLoad(lambdaPerDay: number, meanServiceMin: number): number {
  return (lambdaPerDay / 1440) * meanServiceMin;
}

/**
 * Erlang C delay probability — the chance a new arrival finds all c servers
 * busy. Direct textbook formula, as in the notebook; the a^k/k! terms are
 * accumulated iteratively instead of via factorial() but are the same terms.
 */
export function erlangC(c: number, a: number): number {
  if (a >= c) return 1;
  let sum = 0;
  let term = 1; // a^k / k!, starting at k = 0
  for (let k = 0; k < c; k++) {
    sum += term;
    term *= a / (k + 1);
  }
  // after the loop, term = a^c / c!
  const tail = term * (c / (c - a));
  return tail / (sum + tail);
}

/**
 * P(wait > t). With f = 1 this is Erlang C (M/M/c); with f = (c²ₐ + c²ₛ)/2
 * it is the Allen–Cunneen heuristic, exactly as in NB03's p_wait_gt().
 */
export function pWaitGt(
  c: number,
  a: number,
  t: number,
  meanServiceMin: number,
  f = 1,
): number {
  if (a >= c) return 1;
  return erlangC(c, a) * Math.exp((-(c - a) * t) / (f * meanServiceMin));
}

/** Smallest c with P(wait > t) ≤ target; NB03 searches 1..49, so do we. */
export function minServers(
  a: number,
  t: number,
  meanServiceMin: number,
  f = 1,
  target = MEASURED.target,
): number {
  for (let c = 1; c < 50; c++) {
    if (pWaitGt(c, a, t, meanServiceMin, f) <= target) return c;
  }
  return Infinity;
}

/**
 * "About 1 in N" phrasing for a probability, rounded to numbers a person
 * would actually say. Never used for the meters (those show the full scale);
 * only for the sentences.
 */
export function oneIn(p: number): string {
  if (p >= 0.995) return 'essentially every';
  if (p <= 0.001) return 'fewer than 1 in 1,000';
  const n = 1 / p;
  if (n < 20) return `about 1 in ${Math.round(n)}`;
  if (n < 40) return `about 1 in ${Math.round(n / 5) * 5}`;
  if (n < 200) return `about 1 in ${Math.round(n / 10) * 10}`;
  return `about 1 in ${Math.round(n / 50) * 50}`;
}
