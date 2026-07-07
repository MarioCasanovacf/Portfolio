import { Component, type ErrorInfo, type ReactNode, useMemo, useState } from 'react';
import {
  MEASURED,
  F_TEXTBOOK,
  F_MEASURED,
  offeredLoad,
  pWaitGt,
  minServers,
  oneIn,
} from '~/lib/erlang';

/* ----------------------------------------------------------------- consts --- */
const COUNTS = [1, 2, 3, 4, 5];
const T = MEASURED.thresholdMin; // 30 minutes
const TARGET = MEASURED.target; // 10%

type Mode = 'textbook' | 'measured';

const MODE_F: Record<Mode, number> = {
  textbook: F_TEXTBOOK,
  measured: F_MEASURED,
};

/* -------------------------------------------------------------- formatting --- */
function fmtRate(x: number): string {
  return String(Math.round(x * 100) / 100);
}

function fmtDuration(min: number): string {
  if (min < 60) return `${min} minutes`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m === 0 ? `${min} min (${h} h)` : `${min} min (${h} h ${m} min)`;
}

function fmtPct(p: number): string {
  const v = p * 100;
  if (v >= 99.95) return '100%';
  if (v >= 1) return `${v.toFixed(1)}%`;
  if (v >= 0.005) return `${v.toFixed(2)}%`;
  return '<0.01%';
}

/** "about 1 in 9 incidents waits", with the extremes said like a person would. */
function waitClause(p: number): string {
  if (p >= 0.995) return 'essentially every incident waits';
  if (p <= 0.001) return 'fewer than 1 in 1,000 incidents waits';
  return `${oneIn(p)} incidents waits`;
}

function engineers(c: number): string {
  return c === 1 ? '1 engineer' : `${c} engineers`;
}

/* ------------------------------------------------------ error boundary ------ */
// Same convention as VoteExplorer: an island shouldn't fail silently to a
// blank box. If anything throws, show the message on the page instead.
class ErrorBoundary extends Component<{ children: ReactNode }, { err: Error | null }> {
  state = { err: null as Error | null };
  static getDerivedStateFromError(err: Error) { return { err }; }
  componentDidCatch(err: Error, info: ErrorInfo) { console.error('StaffingCalculator crashed', err, info); }
  render() {
    if (this.state.err) {
      return (
        <div className="sc-state">
          The calculator hit an error: <code>{this.state.err.message}</code>.
          Try a hard refresh; if it persists, this is a bug.
        </div>
      );
    }
    return this.props.children;
  }
}

export default function StaffingCalculator() {
  return (
    <ErrorBoundary>
      <StaffingCalculatorInner />
    </ErrorBoundary>
  );
}

/* ------------------------------------------------------------- component ---- */
function StaffingCalculatorInner() {
  const [lambda, setLambda] = useState(MEASURED.lambdaPerDay); // incidents/day
  const [meanS, setMeanS] = useState(MEASURED.meanServiceMin); // minutes
  const [mode, setMode] = useState<Mode>('textbook');

  const f = MODE_F[mode];
  const a = offeredLoad(lambda, meanS);

  const rows = useMemo(
    () => COUNTS.map((c) => ({ c, p: pWaitGt(c, a, T, meanS, f) })),
    [a, meanS, f],
  );
  const minC = useMemo(() => minServers(a, T, meanS, f), [a, meanS, f]);

  // The one human sentence for the currently relevant count.
  const sentence = useMemo(() => {
    if (!Number.isFinite(minC)) {
      return 'At this load no realistic team meets the target. The queue never drains; the problem is the load, not the roster.';
    }
    if (minC === 1) {
      const p1 = pWaitGt(1, a, T, meanS, f);
      return `One engineer already meets the target: with 1, ${waitClause(p1)} more than half an hour.`;
    }
    if (minC > COUNTS[COUNTS.length - 1]) {
      const p5 = pWaitGt(5, a, T, meanS, f);
      return `Even with 5 engineers, ${waitClause(p5)} more than half an hour. Meeting the target takes ${minC}.`;
    }
    const pBelow = pWaitGt(minC - 1, a, T, meanS, f);
    const pMin = pWaitGt(minC, a, T, meanS, f);
    // pMin ≤ the 10% target by construction, so the short form is always safe.
    const second = pMin <= 0.001 ? 'fewer than 1 in 1,000' : oneIn(pMin);
    return `With ${engineers(minC - 1)}, ${waitClause(pBelow)} more than half an hour. With ${minC}, ${second}.`;
  }, [a, meanS, f, minC]);

  return (
    <div className="sc">
      {/* ------------------------------------------------------- controls --- */}
      <section className="sc-controls" aria-label="Calculator controls">
        <div className="sc-control">
          <div className="sc-control__head">
            <label className="sc-control__label" htmlFor="sc-lambda">
              Incidents arriving per day
            </label>
            <output className="sc-control__value" htmlFor="sc-lambda">
              {fmtRate(lambda)} a day
            </output>
          </div>
          <input
            id="sc-lambda"
            type="range"
            min={1}
            max={15}
            step={0.1}
            value={lambda}
            onChange={(e) => setLambda(Number(e.target.value))}
          />
          <p className="sc-control__hint">
            The worst week in this capture ran at 5.14 a day (36 incidents, June 7–13).
          </p>
        </div>

        <div className="sc-control">
          <div className="sc-control__head">
            <label className="sc-control__label" htmlFor="sc-means">
              How long a fix usually takes
            </label>
            <output className="sc-control__value" htmlFor="sc-means">
              {fmtDuration(meanS)}
            </output>
          </div>
          <input
            id="sc-means"
            type="range"
            min={30}
            max={360}
            step={1}
            value={meanS}
            onChange={(e) => setMeanS(Number(e.target.value))}
          />
          <p className="sc-control__hint">
            The average fix in that week took 156 minutes, long incidents included.
          </p>
        </div>

        <div className="sc-control sc-control--toggle">
          <div className="sc-control__head">
            <span className="sc-control__label" id="sc-mode-label">
              How predictable are your fixes?
            </span>
          </div>
          <div className="sc-toggle" role="radiogroup" aria-labelledby="sc-mode-label">
            <button
              type="button"
              role="radio"
              aria-checked={mode === 'textbook'}
              className={mode === 'textbook' ? 'sc-toggle__opt is-on' : 'sc-toggle__opt'}
              onClick={() => setMode('textbook')}
            >
              <span className="sc-toggle__name">Textbook world</span>
              <span className="sc-toggle__sub">every fix looks alike</span>
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={mode === 'measured'}
              className={mode === 'measured' ? 'sc-toggle__opt is-on' : 'sc-toggle__opt'}
              onClick={() => setMode('measured')}
            >
              <span className="sc-toggle__name">This data</span>
              <span className="sc-toggle__sub">one fix in twenty takes a day</span>
            </button>
          </div>
          <p className="sc-control__hint">
            The textbook assumes the next fix takes about as long as the last one.
            The capture disagrees: most fixes take an hour, and one in twenty takes
            a day or more. Same arrivals, same average fix — only the spread changes.
          </p>
        </div>
      </section>

      {/* -------------------------------------------------------- results --- */}
      <section className="sc-results" aria-label="Results">
        <h2 className="sc-results__title">How often does an incident wait more than 30 minutes?</h2>
        <p className="sc-results__target">
          The target, taken from the case study: at most 1 in 10 incidents waits
          that long (so 90% get a responder within half an hour).
        </p>

        <div className="sc-meters">
          {rows.map(({ c, p }) => {
            const meets = p <= TARGET;
            const isAnswer = c === minC;
            return (
              <div className={isAnswer ? 'sc-meter is-answer' : 'sc-meter'} key={c}>
                <div className="sc-meter__label">{engineers(c)}</div>
                <div
                  className="sc-meter__track"
                  role="img"
                  aria-label={`${engineers(c)}: ${fmtPct(p)} of incidents wait more than 30 minutes${meets ? ' — meets the target' : ''}`}
                >
                  <span
                    className={meets ? 'sc-meter__fill is-ok' : 'sc-meter__fill'}
                    style={{ width: `${Math.min(100, p * 100)}%` }}
                  />
                  <span className="sc-meter__tick" aria-hidden="true" />
                </div>
                <div className="sc-meter__pct">{fmtPct(p)}</div>
                <div className="sc-meter__note">
                  {isAnswer ? 'smallest team that meets the target' : ''}
                </div>
              </div>
            );
          })}
          <div className="sc-scale" aria-hidden="true">
            <span>0%</span>
            <span className="sc-scale__target">target · 10%</span>
            <span>full scale · 100%</span>
          </div>
        </div>

        <p className="sc-sentence" aria-live="polite">{sentence}</p>
      </section>

      {/* ----------------------------------------------------- disclosure --- */}
      <details className="sc-how">
        <summary>How is this computed?</summary>
        <div className="sc-how__body">
          <p>
            The bars come from Erlang's 1917 delay formula for a queue with{' '}
            <var>c</var> servers. The chance that a new incident finds everyone
            busy is
          </p>
          <p className="sc-how__math">
            C(c, a) = [ a<sup>c</sup>/c! · c/(c−a) ] ÷ [ Σ<sub>k=0…c−1</sub>{' '}
            a<sup>k</sup>/k! + a<sup>c</sup>/c! · c/(c−a) ]
          </p>
          <p>
            where <var>a</var> = λ·S is the offered load in erlangs (arrivals per
            minute × mean fix minutes). The probability that it then waits longer
            than <var>t</var> = 30 minutes is
          </p>
          <p className="sc-how__math">
            P(wait &gt; t) = C(c, a) · e<sup>−(c−a)·t / (f·S)</sup>
          </p>
          <p>
            The switch sets <var>f</var>. In the textbook world arrivals are Poisson
            and fix times exponential, so <var>f</var> = 1 and this is plain Erlang
            C. In the measured world <var>f</var> is the Allen–Cunneen scaling
            (c²ₐ + c²ₛ)/2 = (1.65 + 13.47)/2 = 7.56, where c²ₐ is the squared
            coefficient of variation of the arrivals and c²ₛ that of the fix times,
            both measured in the peak week rather than assumed. At the defaults
            (λ = 5.14/day, S = 156 min, so a = 0.557 erlangs) Erlang C puts two
            engineers at 9.2% and Allen–Cunneen puts them at 11.7%, with three at
            1.9% — the full derivation, the assumption tests that justify the
            corrected column, and the bootstrap that turns the point answer into a
            range (two to four engineers, plan for three) live in{' '}
            <a href={`${import.meta.env.BASE_URL.replace(/\/?$/, '/')}case-studies/cloud-ops/#textbook-team-measured-team`}>
              Section 3 of the case study
            </a>{' '}
            and in notebook NB03.
          </p>
        </div>
      </details>

      <p className="sc-note">
        This is a model with declared assumptions, calibrated to nine weeks of real
        status-page data (787 incidents from 18 providers; the defaults are the
        worst observed week). It ranks staffing options against each other; it does
        not guarantee outcomes. I trust the comparison between the two worlds more
        than I trust any single number on this page.
      </p>
    </div>
  );
}
