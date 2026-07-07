import { Component, type ErrorInfo, type ReactNode, useEffect, useMemo, useState } from 'react';

/* ------------------------------------------------------------------ types --- */
type Bloc = 'government' | 'opposition' | 'other';
interface Party { code: string; full: string; bloc: Bloc }
interface Deputy { id: string; name: string; party: string }
interface Tally { for: number; against: number; abstain: number; present: number; absent: number }
interface Proposal { id: string; n: number; date: string; title: string; totals: Tally; byParty: Record<string, Tally> }
interface Data {
  legislature: number;
  parties: Party[];
  deputies: Deputy[];
  proposals: Proposal[];
  ballots: Record<string, string>;
}

/* ----------------------------------------------------------------- consts --- */
// Single-char sense codes used in the ballot strings.
const SENSE: Record<string, { label: string; color: string }> = {
  F: { label: 'For', color: '#2E4A3F' },      // forest
  C: { label: 'Against', color: '#6E1F1F' },  // oxblood
  B: { label: 'Abstain', color: '#A87333' },  // ochre
  X: { label: 'Absent', color: '#B8B0A2' },   // muted
  P: { label: 'Present', color: '#6B655C' },
  '-': { label: '—', color: '#D8D0C2' },
};
const SEGMENTS: Array<[keyof Tally, string]> = [
  ['for', '#2E4A3F'], ['against', '#6E1F1F'], ['abstain', '#A87333'],
  ['present', '#6B655C'], ['absent', '#B8B0A2'],
];
const BLOC_LABEL: Record<Bloc, string> = {
  government: 'Government', opposition: 'Opposition', other: 'Other',
};
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function fmtDate(iso: string | null): string {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}
function tallyTotal(t: Tally): number {
  return t.for + t.against + t.abstain + t.present + t.absent;
}

/* ------------------------------------------------------ error boundary ------ */
// A complex island shouldn't fail silently to a blank box. If anything throws,
// show the message on the page instead.
class ErrorBoundary extends Component<{ children: ReactNode }, { err: Error | null }> {
  state = { err: null as Error | null };
  static getDerivedStateFromError(err: Error) { return { err }; }
  componentDidCatch(err: Error, info: ErrorInfo) { console.error('VoteExplorer crashed', err, info); }
  render() {
    if (this.state.err) {
      return (
        <div className="vx-state">
          The vote explorer hit an error: <code>{this.state.err.message}</code>.
          Try a hard refresh; if it persists, this is a bug.
        </div>
      );
    }
    return this.props.children;
  }
}

export default function VoteExplorer() {
  return (
    <ErrorBoundary>
      <VoteExplorerInner />
    </ErrorBoundary>
  );
}

/* ------------------------------------------------------------- component ---- */
function VoteExplorerInner() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [depQuery, setDepQuery] = useState('');
  const [partyFilter, setPartyFilter] = useState<string>('all');
  const [senseFilter, setSenseFilter] = useState<string>('all');
  const [openDeputy, setOpenDeputy] = useState<string | null>(null);

  useEffect(() => {
    fetch(import.meta.env.BASE_URL.replace(/\/?$/, '/') + 'data/legislative-votes.json')
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((d: Data) => {
        d.proposals.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : b.n - a.n));
        setData(d);
        setSelectedId(d.proposals[0]?.id ?? null);
      })
      .catch(() => setError(true));
  }, []);

  // index of each deputy within the ballot strings
  const depIndex = useMemo(() => {
    const m = new Map<string, number>();
    data?.deputies.forEach((dp, i) => m.set(dp.id, i));
    return m;
  }, [data]);

  const filteredProposals = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    if (!q) return data.proposals;
    return data.proposals.filter(
      (p) => p.title.toLowerCase().includes(q) || fmtDate(p.date).toLowerCase().includes(q) || String(p.n) === q,
    );
  }, [data, query]);

  const selected = useMemo(
    () => data?.proposals.find((p) => p.id === selectedId) ?? null,
    [data, selectedId],
  );
  const ballot = selected ? data?.ballots[selected.id] ?? '' : '';

  const deputyRows = useMemo(() => {
    if (!data || !selected) return [];
    const q = depQuery.trim().toLowerCase();
    const rows = data.deputies.map((dp, i) => ({ dp, sense: ballot[i] || '-' }));
    return rows.filter(({ dp, sense }) => {
      if (q && !dp.name.toLowerCase().includes(q)) return false;
      if (partyFilter !== 'all' && dp.party !== partyFilter) return false;
      if (senseFilter !== 'all' && sense !== senseFilter) return false;
      return true;
    });
  }, [data, selected, ballot, depQuery, partyFilter, senseFilter]);

  // lifetime record for the expanded deputy
  const deputyRecord = useMemo(() => {
    if (!data || !openDeputy) return null;
    const i = depIndex.get(openDeputy);
    if (i == null) return null;
    const counts: Record<string, number> = { F: 0, C: 0, B: 0, X: 0, P: 0 };
    let total = 0;
    for (const p of data.proposals) {
      const ch = data.ballots[p.id]?.[i];
      if (ch && ch !== '-') { counts[ch] = (counts[ch] || 0) + 1; total++; }
    }
    return { counts, total };
  }, [data, openDeputy, depIndex]);

  if (error) {
    return <div className="vx-state">Couldn’t load the vote data. Try a hard refresh.</div>;
  }
  if (!data || !selected) {
    return <div className="vx-state">Loading 274 votes…</div>;
  }

  const partyByCode = new Map(data.parties.map((p) => [p.code, p]));
  const blocs: Bloc[] = ['government', 'opposition', 'other'];

  return (
    <div className="vx">
      {/* legend */}
      <div className="vx-legend">
        {(['F', 'C', 'B', 'X'] as const).map((k) => (
          <span key={k} className="vx-legend__item">
            <span className="vx-swatch" style={{ background: SENSE[k].color }} />
            {SENSE[k].label}
          </span>
        ))}
      </div>

      <div className="vx-grid">
        {/* -------- proposal list -------- */}
        <aside className="vx-list" aria-label="Proposals">
          <input
            className="vx-search"
            placeholder="Search proposals…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="vx-list__count">{filteredProposals.length} of {data.proposals.length} votes</div>
          <ul className="vx-list__items">
            {filteredProposals.map((p) => {
              const t = p.totals;
              const lead = t.for >= t.against ? 'for' : 'against';
              return (
                <li key={p.id}>
                  <button
                    className={'vx-item' + (p.id === selected.id ? ' is-active' : '')}
                    onClick={() => { setSelectedId(p.id); setOpenDeputy(null); }}
                  >
                    <span className="vx-item__meta">
                      <span className="vx-item__n">#{p.n}</span>
                      <span className="vx-item__date">{fmtDate(p.date)}</span>
                      <span className={'vx-item__lead vx-item__lead--' + lead}>
                        {t.for}–{t.against}
                      </span>
                    </span>
                    <span className="vx-item__title">{p.title}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        {/* -------- detail -------- */}
        <section className="vx-detail">
          <header className="vx-detail__head">
            <div className="vx-eyebrow">Vote #{selected.n} · {fmtDate(selected.date)}</div>
            <h3 className="vx-detail__title">{selected.title}</h3>
            <div className="vx-totals">
              {(['for', 'against', 'abstain', 'absent'] as const).map((k) => (
                <span key={k} className="vx-total">
                  <span className="vx-total__n">{selected.totals[k]}</span>
                  <span className="vx-total__k">{k}</span>
                </span>
              ))}
            </div>
          </header>

          {/* per-party breakdown */}
          <div className="vx-parties">
            {blocs.map((bloc) => {
              const ps = data.parties.filter((p) => p.bloc === bloc && selected.byParty[p.code]);
              if (!ps.length) return null;
              return (
                <div key={bloc} className="vx-bloc">
                  <div className="vx-bloc__label">{BLOC_LABEL[bloc]}</div>
                  {ps.map((p) => {
                    const t = selected.byParty[p.code];
                    const tot = tallyTotal(t) || 1;
                    return (
                      <div key={p.code} className="vx-prow">
                        <span className="vx-prow__code" title={p.full}>{p.code}</span>
                        <span className="vx-bar">
                          {SEGMENTS.map(([k, color]) =>
                            t[k] > 0 ? (
                              <span
                                key={k}
                                className="vx-bar__seg"
                                style={{ width: (t[k] / tot) * 100 + '%', background: color }}
                                title={`${t[k]} ${k}`}
                              />
                            ) : null,
                          )}
                        </span>
                        <span className="vx-prow__for">{t.for}</span>
                        <span className="vx-prow__against">{t.against}</span>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* deputy table */}
          <div className="vx-deputies">
            <div className="vx-deputies__controls">
              <input
                className="vx-search vx-search--sm"
                placeholder="Find a deputy…"
                value={depQuery}
                onChange={(e) => setDepQuery(e.target.value)}
              />
              <select className="vx-select" value={partyFilter} onChange={(e) => setPartyFilter(e.target.value)}>
                <option value="all">All parties</option>
                {data.parties.map((p) => <option key={p.code} value={p.code}>{p.code}</option>)}
              </select>
              <select className="vx-select" value={senseFilter} onChange={(e) => setSenseFilter(e.target.value)}>
                <option value="all">All votes</option>
                <option value="F">For</option>
                <option value="C">Against</option>
                <option value="B">Abstain</option>
                <option value="X">Absent</option>
              </select>
              <span className="vx-deputies__count">{deputyRows.length} deputies</span>
            </div>

            <ul className="vx-rows">
              {deputyRows.map(({ dp, sense }) => {
                const open = openDeputy === dp.id;
                return (
                  <li key={dp.id} className={'vx-row' + (open ? ' is-open' : '')}>
                    <button className="vx-row__btn" onClick={() => setOpenDeputy(open ? null : dp.id)}>
                      <span className="vx-row__name">{dp.name}</span>
                      <span className="vx-row__party">{dp.party}</span>
                      <span className="vx-chip" style={{ color: SENSE[sense].color, borderColor: SENSE[sense].color }}>
                        {SENSE[sense].label}
                      </span>
                    </button>
                    {open && deputyRecord && (
                      <div className="vx-record">
                        Full LXVI record over {deputyRecord.total} votes cast:{' '}
                        {(['F', 'C', 'B', 'X'] as const).map((k, idx) => (
                          <span key={k}>
                            {idx > 0 && ' · '}
                            <b style={{ color: SENSE[k].color }}>{deputyRecord.counts[k]}</b> {SENSE[k].label.toLowerCase()}
                          </span>
                        ))}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
