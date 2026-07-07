"""SITL scraper — per-deputy roll-call votes from the Chamber of Deputies.

`sitl.diputados.gob.mx` is the only live source with true per-deputy roll-call
data for the recent legislatures (LXIV-LXVI); dipMex's structured votes stop
around legislature 62. This client captures, for a legislature, every vote event
and every deputy's vote on it.

Endpoint structure (verified live, three levels per legislature):
  1. Period index : {LEG}_leg/votaciones_por_periodonp{leg}.php          -> pert ids
  2. Vote list    : votacionesxperiodonp{leg}.php?pert=N                  -> votaciont ids
  3. Per-deputy   : listados_votacionesnp{leg}.php?partidot=P&votaciont=V -> rows
        columns: '# | Diputado(a) | Sentido del voto'
        names  : "APELLIDO1 APELLIDO2 NOMBRE" (surnames first, NO comma)
        party  : from the page header (one page per partidot)
        each name links ...?iddipt=NNN  (stable per-deputy id within a legislature)
        senses : A favor / En contra / Abstención / Ausente / Solo asistencia

Notes:
  * SITL blocks bot/default User-Agents -> a browser UA is forced here.
  * ~votes x 6 parties requests per legislature, so it rate-limits politely.
  * **Incremental & idempotent**: a per-legislature manifest records the
    votaciont ids already captured; a re-run fetches ONLY new votes and appends.
    Designed so new sessions/legislatures ingest without a rebuild.

This module was written against the verified endpoint spec; the first live run
(from a network that resolves the gov host) is its validation. Raw HTML for every
fetched page is persisted under the landing zone for lineage and debugging.
"""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

import structlog
from bs4 import BeautifulSoup

from capture.base import BaseScraper
from config import CaptureSettings

logger = structlog.get_logger(__name__)

# SITL rejects non-browser User-Agents; force a realistic one.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Legislature number -> SITL slug (lowercase in filenames, UPPERCASE in the path).
LEGISLATURES: dict[int, str] = {64: "lxiv", 65: "lxv", 66: "lxvi"}

# `partidot` is the per-vote party-group/page index (NOT a stable party id — the
# same value maps to different parties in different votes, and one party can span
# several pages). The party name is read from each page; the scan is defensive.
MAX_PARTIDOT = 30          # upper bound for the defensive upward scan
EMPTY_RUN_STOP = 4         # stop scanning after this many CONSECUTIVE empty pages

# "Sentido del voto" -> standardized vote_cast (matches dipMex's enum; the
# attendance-only sense is kept distinct as PRESENT so nothing is lost).
VOTE_SENSE_MAP: dict[str, str] = {
    "a favor": "FOR",
    "en contra": "AGAINST",
    "abstención": "ABSTAIN",
    "abstencion": "ABSTAIN",
    "ausente": "ABSENT",
    "solo asistencia": "PRESENT",
}

VOTE_FIELDS = [
    "legislature", "pert", "votaciont", "iddipt",
    "legislator_name", "party", "vote_sense", "vote_cast",
]

# Per-vote metadata + official per-party tallies, both read from the estadistico
# (per-vote summary) page — captured alongside the per-deputy votes so the dated
# dimension/fact have a real vote_date, and so our per-deputy aggregation can be
# cross-checked against SITL's official counts.
META_FIELDS = ["legislature", "pert", "votaciont", "vote_date", "vote_date_raw", "title"]
TALLY_FIELDS = [
    "legislature", "votaciont", "party",
    "a_favor", "en_contra", "abstencion", "solo_asistencia", "ausente", "total",
]


class SitlScraper(BaseScraper):
    """Capture per-deputy roll-call votes from SITL for one legislature."""

    def __init__(self, legislature: int = 66, settings: CaptureSettings | None = None) -> None:
        super().__init__(settings)
        if legislature not in LEGISLATURES:
            raise ValueError(f"Unsupported legislature {legislature}; expected one of {list(LEGISLATURES)}")
        self.legislature = legislature
        self.slug = LEGISLATURES[legislature]            # e.g. "lxvi"
        self.path_seg = self.slug.upper()                # e.g. "LXVI"
        self.base = self.settings.base_url_diputados.rstrip("/")
        # SITL blocks the default academic UA — override with a browser UA.
        self.client.headers["User-Agent"] = BROWSER_UA
        self.out_dir = self.settings.output_dir / "sitl" / self.slug
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.out_dir / "manifest.json"
        self.votes_csv = self.out_dir / f"sitl_votes_{self.slug}.csv"
        self.meta_csv = self.out_dir / f"sitl_vote_meta_{self.slug}.csv"
        self.tallies_csv = self.out_dir / f"sitl_tallies_{self.slug}.csv"
        self.log = logger.bind(scraper="SitlScraper", legislature=legislature)

    # --- URL builders -------------------------------------------------------
    def _period_index_url(self) -> str:
        return f"{self.base}/{self.path_seg}_leg/votaciones_por_periodonp{self.slug}.php"

    def _vote_list_url(self, pert: int) -> str:
        return f"{self.base}/{self.path_seg}_leg/votacionesxperiodonp{self.slug}.php?pert={pert}"

    def _deputy_url(self, votaciont: int, partidot: int) -> str:
        return (
            f"{self.base}/{self.path_seg}_leg/listados_votacionesnp{self.slug}.php"
            f"?partidot={partidot}&votaciont={votaciont}"
        )

    def _estadistico_url(self, votaciont: int) -> str:
        # Per-vote summary page (linked from the vote list); it exposes the exact
        # partidot ids for this vote, and is kept as lineage.
        return (
            f"{self.base}/{self.path_seg}_leg/estadistico_votacionnp{self.slug}.php"
            f"?votaciont={votaciont}"
        )

    # --- helpers ------------------------------------------------------------
    def _get_html(self, url: str) -> str:
        """Fetch a URL (with the base class's retries), then rate-limit politely."""
        html = self.fetch(url).text
        time.sleep(self.settings.rate_limit_delay)
        return html

    def _load_manifest(self) -> set[int]:
        if self.manifest_path.exists():
            return set(json.loads(self.manifest_path.read_text()).get("captured_votaciont", []))
        return set()

    def _save_manifest(self, captured: set[int]) -> None:
        self.manifest_path.write_text(json.dumps(
            {"legislature": self.legislature, "captured_votaciont": sorted(captured)}, indent=2
        ))

    # --- parsing (faithful to the verified HTML structure) ------------------
    @staticmethod
    def _extract_ids(html: str, param: str) -> list[int]:
        """Distinct integer values of `?{param}=N` links, in first-seen order."""
        seen: dict[int, None] = {}
        for m in re.finditer(rf"{param}=(\d+)", html):
            seen.setdefault(int(m.group(1)), None)
        return list(seen)

    @staticmethod
    def _party_label(soup: BeautifulSoup) -> str:
        """Party name = the stripped string immediately before the 'Diputado(a)'
        table header (verified stable across votes). The page title's 'Grupo
        Parlamentario LXVI' must NOT be used — it is not the group name."""
        strings = list(soup.stripped_strings)
        for i, s in enumerate(strings):
            if s.startswith("Diputado") and i > 0:
                return strings[i - 1]
        return ""

    def _parse_deputy_page(self, html: str, pert: int, votaciont: int) -> list[dict]:
        """Parse one party-group page -> standardized vote rows.

        Each deputy is a table row with EXACTLY three cells (#, name, sentido).
        SITL also emits a wrapper <tr> holding the whole flattened table; the
        3-cell guard rejects it (which also kills the duplicate row it used to
        produce)."""
        soup = BeautifulSoup(html, "lxml")
        party = self._party_label(soup)
        rows: list[dict] = []
        for tr in soup.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(cells) != 3:
                continue
            link = tr.find("a", href=re.compile(r"iddipt=\d+"))
            if not link:
                continue
            iddipt = int(re.search(r"iddipt=(\d+)", link["href"]).group(1))
            name = " ".join(link.get_text(" ", strip=True).split()) or cells[1]
            sense = cells[-1]
            rows.append({
                "legislature": self.legislature,
                "pert": pert,
                "votaciont": votaciont,
                "iddipt": iddipt,
                "legislator_name": name,
                "party": party,
                "vote_sense": sense,
                "vote_cast": VOTE_SENSE_MAP.get(sense.strip().lower(), ""),
            })
        return rows

    # --- per-vote summary (estadistico): date, title, partidot ids, tallies -
    SPANISH_MONTHS = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }

    @classmethod
    def _parse_date(cls, raw: str) -> str:
        """'28-Mayo-2026' -> ISO '2026-05-28'; '' if unrecognized."""
        m = re.match(r"(\d{1,2})-([A-Za-zÁÉÍÓÚáéíóúñ]+)-(\d{4})", raw.strip())
        if not m:
            return ""
        day, mon, year = m.group(1), m.group(2).lower(), m.group(3)
        month = cls.SPANISH_MONTHS.get(mon)
        return f"{year}-{month:02d}-{int(day):02d}" if month else ""

    @classmethod
    def _parse_estadistico(cls, html: str, legislature: int, votaciont: int, pert: int) -> dict:
        """Parse a per-vote summary page -> {partidots, vote_date(+raw), title,
        tallies}. Pure (no I/O), so the same logic also backfills saved pages.

        Layout: a title string immediately followed by the date 'DD-Mes-AAAA',
        then a 7-column table 'GRUPO PARLAMENTARIO | A FAVOR | EN CONTRA |
        ABSTENCIÓN | SOLO ASISTENCIA | AUSENTE | TOTAL' with one row per party."""
        soup = BeautifulSoup(html, "lxml")
        strings = list(soup.stripped_strings)
        date_raw, title = "", ""
        for i, s in enumerate(strings):
            if re.match(r"^\d{1,2}-[A-Za-zÁÉÍÓÚáéíóúñ]+-\d{4}$", s):
                date_raw = s
                title = strings[i - 1] if i > 0 else ""
                break

        partidots: list[int] = []
        for m in re.finditer(r"partidot=(\d+)", html):
            v = int(m.group(1))
            if v not in partidots:
                partidots.append(v)

        tallies: list[dict] = []
        for tr in soup.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(cells) != 7 or not all(c.isdigit() for c in cells[1:]):
                continue                                  # skips header + wrapper rows
            if cells[0].strip().upper().startswith("TOTAL"):
                continue                                  # grand-total row, not a party
            n = [int(c) for c in cells[1:]]
            tallies.append({
                "legislature": legislature, "votaciont": votaciont, "party": cells[0],
                "a_favor": n[0], "en_contra": n[1], "abstencion": n[2],
                "solo_asistencia": n[3], "ausente": n[4], "total": n[5],
            })
        return {
            "legislature": legislature, "pert": pert, "votaciont": votaciont,
            "vote_date": cls._parse_date(date_raw), "vote_date_raw": date_raw,
            "title": title, "partidots": partidots, "tallies": tallies,
        }

    def _fetch_estadistico(self, pert: int, votaciont: int) -> dict:
        """Fetch+save the per-vote summary and parse it. On failure returns a dict
        with empty partidots (the caller then falls back to a partidot scan)."""
        try:
            html = self._get_html(self._estadistico_url(votaciont))
        except Exception:
            self.log.warning("estadistico_failed", votaciont=votaciont)
            return {"legislature": self.legislature, "pert": pert, "votaciont": votaciont,
                    "vote_date": "", "vote_date_raw": "", "title": "",
                    "partidots": [], "tallies": []}
        self.save_raw(html, f"sitl/{self.slug}/raw/estadistico_v{votaciont}.html")
        return self._parse_estadistico(html, self.legislature, votaciont, pert)

    def _capture_vote(self, pert: int, votaciont: int) -> tuple[list[dict], dict]:
        """Capture one vote -> (per-deputy rows deduped by iddipt, vote metadata).

        `partidot` is a per-vote page index (not a stable party id), and empty
        pages can sit between real ones — so we do NOT break on the first empty.
        We first follow the exact partidot ids the per-vote summary links to, then
        scan upward for anything it omitted, stopping only after a run of
        consecutive empties."""
        rows: dict[int, dict] = {}

        def consume(partidot: int) -> bool:
            url = self._deputy_url(votaciont, partidot)
            try:
                html = self._get_html(url)
            except Exception:
                self.log.warning("deputy_page_failed", votaciont=votaciont, partidot=partidot)
                return False
            self.save_raw(html, f"sitl/{self.slug}/raw/v{votaciont}_p{partidot}.html")
            page_rows = self._parse_deputy_page(html, pert, votaciont)
            for r in page_rows:
                rows.setdefault(r["iddipt"], r)   # dedup by deputy within the vote
            return bool(page_rows)

        meta = self._fetch_estadistico(pert, votaciont)                 # date, title, partidots, tallies

        tried: set[int] = set()
        for partidot in meta.get("partidots", []):                      # summary-linked pages
            tried.add(partidot)
            consume(partidot)

        empties = 0                                                     # defensive upward scan
        for partidot in range(1, MAX_PARTIDOT + 1):
            if partidot in tried:
                continue
            tried.add(partidot)
            if consume(partidot):
                empties = 0
            else:
                empties += 1
                if empties >= EMPTY_RUN_STOP:
                    break

        return list(rows.values()), meta

    @staticmethod
    def _append_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
        if not rows:
            return
        write_header = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if write_header:
                w.writeheader()
            w.writerows(rows)

    def _append_votes(self, rows: list[dict]) -> None:
        self._append_rows(self.votes_csv, VOTE_FIELDS, rows)

    def _append_meta(self, meta: dict) -> None:
        self._append_rows(self.meta_csv, META_FIELDS, [meta])

    def _append_tallies(self, tallies: list[dict]) -> None:
        self._append_rows(self.tallies_csv, TALLY_FIELDS, tallies)

    def scrape(self) -> list[Path]:
        """Incrementally capture every per-deputy vote for the legislature."""
        captured = self._load_manifest()
        self.log.info("sitl.start", already_captured=len(captured))

        index_html = self._get_html(self._period_index_url())
        self.save_raw(index_html, f"sitl/{self.slug}/raw/period_index.html")
        perts = self._extract_ids(index_html, "pert")
        self.log.info("sitl.periods", n=len(perts), perts=perts)

        new_total = 0
        for pert in perts:
            list_html = self._get_html(self._vote_list_url(pert))
            self.save_raw(list_html, f"sitl/{self.slug}/raw/votelist_pert{pert}.html")
            votacionts = self._extract_ids(list_html, "votaciont")
            todo = [v for v in votacionts if v not in captured]
            self.log.info("sitl.period", pert=pert, votes=len(votacionts), new=len(todo))

            for votaciont in todo:
                rows, meta = self._capture_vote(pert, votaciont)
                if rows:
                    self._append_votes(rows)
                    self._append_meta(meta)
                    self._append_tallies(meta.get("tallies", []))
                    captured.add(votaciont)
                    self._save_manifest(captured)   # checkpoint after every vote -> resumable
                    new_total += len(rows)
                    self.log.info("sitl.vote_done", votaciont=votaciont,
                                  rows=len(rows), date=meta.get("vote_date", ""))

        self.log.info("sitl.done", new_rows=new_total, total_votes=len(captured), csv=str(self.votes_csv))
        return [self.votes_csv, self.meta_csv, self.tallies_csv, self.manifest_path]


if __name__ == "__main__":  # pragma: no cover
    import sys

    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))
    leg = int(sys.argv[1]) if len(sys.argv) > 1 else 66
    with SitlScraper(legislature=leg) as scraper:
        scraper.scrape()
