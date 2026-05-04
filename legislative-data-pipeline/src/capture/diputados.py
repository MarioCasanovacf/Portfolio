"""Scraper for the Cámara de Diputados (SITL and Gaceta Parlamentaria).

Extracts voting records, legislator profiles, and attendance data from
the official Chamber of Deputies websites. Since there is no official API,
this module scrapes structured HTML tables.
"""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from bs4 import BeautifulSoup, Tag

from capture.base import BaseScraper
from config import CaptureSettings

logger = structlog.get_logger(__name__)

# Legislative periods to scrape (Roman numeral ID → numeric).
LEGISLATURES: dict[str, int] = {
    "LXIV": 64,
    "LXV": 65,
    "LXVI": 66,
}


@dataclass
class VoteRecord:
    """A single roll-call vote extracted from SITL."""

    legislature: int
    session_date: str
    vote_id: str
    description: str
    votes_for: int = 0
    votes_against: int = 0
    abstentions: int = 0
    absences: int = 0
    detail_url: str = ""
    individual_votes: list[dict[str, str]] = field(default_factory=list)


class DiputadosScraper(BaseScraper):
    """Scrape voting records from the Chamber of Deputies SITL system.

    The SITL (Sistema de Información para la Transparencia Legislativa) publishes
    roll-call votes as HTML tables organized by legislative session. This scraper
    extracts the vote summaries and individual legislator votes.
    """

    VOTES_URL = "https://www.diputados.gob.mx/Votaciones.htm"
    SITL_BASE = "https://sitl.diputados.gob.mx/LXVI_leg"

    def __init__(self, settings: CaptureSettings | None = None) -> None:
        super().__init__(settings)

    def _parse_vote_table(self, html: str, legislature: int) -> list[VoteRecord]:
        """Parse an HTML page containing a table of vote summaries.

        Args:
            html: Raw HTML content.
            legislature: Numeric legislature identifier.

        Returns:
            List of parsed vote records.
        """
        soup = BeautifulSoup(html, "lxml")
        records: list[VoteRecord] = []

        # SITL tables use <tr> rows with vote data in <td> cells.
        rows = soup.select("table tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            # Extract text, stripping whitespace.
            cell_text = [c.get_text(strip=True) for c in cells]

            # Look for rows that contain vote counts (digits in columns 2-5).
            if not any(re.match(r"^\d+$", t) for t in cell_text[1:5]):
                continue

            # Extract the detail link if present.
            link_tag = row.find("a", href=True)
            detail_url = ""
            if isinstance(link_tag, Tag) and link_tag.get("href"):
                href = str(link_tag["href"])
                if not href.startswith("http"):
                    href = f"{self.SITL_BASE}/{href}"
                detail_url = href

            try:
                record = VoteRecord(
                    legislature=legislature,
                    session_date=cell_text[0] if cell_text[0] else "",
                    vote_id=f"leg{legislature}_{len(records)}",
                    description=cell_text[1] if len(cell_text) > 5 else "",
                    votes_for=int(cell_text[-4]) if cell_text[-4].isdigit() else 0,
                    votes_against=int(cell_text[-3]) if cell_text[-3].isdigit() else 0,
                    abstentions=int(cell_text[-2]) if cell_text[-2].isdigit() else 0,
                    absences=int(cell_text[-1]) if cell_text[-1].isdigit() else 0,
                    detail_url=detail_url,
                )
                records.append(record)
            except (ValueError, IndexError):
                self.log.warning("skipped_malformed_row", cells=cell_text)
                continue

        return records

    def scrape_legislature_votes(self, legislature_roman: str) -> list[VoteRecord]:
        """Scrape all vote records for a given legislature.

        Args:
            legislature_roman: Roman numeral identifier (e.g., "LXVI").

        Returns:
            List of vote records for the legislature.
        """
        legislature_num = LEGISLATURES.get(legislature_roman, 0)
        self.log.info("scraping_legislature", legislature=legislature_roman, num=legislature_num)

        try:
            response = self.fetch(self.VOTES_URL, params={"leg": legislature_roman})
            records = self._parse_vote_table(response.text, legislature_num)
            self.log.info(
                "parsed_votes",
                legislature=legislature_roman,
                count=len(records),
            )
            return records
        except Exception:
            self.log.exception("scrape_failed", legislature=legislature_roman)
            return []

    def _serialize_votes(self, records: list[VoteRecord]) -> str:
        """Convert vote records to CSV format.

        Args:
            records: List of vote records to serialize.

        Returns:
            CSV string with headers.
        """
        headers = [
            "legislature",
            "session_date",
            "vote_id",
            "description",
            "votes_for",
            "votes_against",
            "abstentions",
            "absences",
            "detail_url",
        ]
        lines = [",".join(headers)]
        for r in records:
            row = [
                str(r.legislature),
                r.session_date,
                r.vote_id,
                f'"{r.description}"',
                str(r.votes_for),
                str(r.votes_against),
                str(r.abstentions),
                str(r.absences),
                r.detail_url,
            ]
            lines.append(",".join(row))
        return "\n".join(lines)

    def scrape(self) -> list[Path]:
        """Scrape voting records for all configured legislatures.

        Returns:
            List of paths to saved CSV files.
        """
        self.log.info("starting_diputados_scrape", legislatures=list(LEGISLATURES.keys()))
        results: list[Path] = []

        for leg_roman in LEGISLATURES:
            records = self.scrape_legislature_votes(leg_roman)
            if records:
                csv_data = self._serialize_votes(records)
                path = self.save_raw(csv_data, f"diputados/votes_{leg_roman}.csv")
                results.append(path)
            time.sleep(self.settings.rate_limit_delay)

        self.log.info("diputados_scrape_complete", files=len(results))
        return results
