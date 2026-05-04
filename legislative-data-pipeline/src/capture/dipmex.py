"""Client for the dipMex academic dataset (GitHub: emagar/dipMex).

DipMex provides structured roll-call vote data for the Mexican Chamber of Deputies.
This is the most reliable structured source for legislative voting analysis.
"""

import time
from pathlib import Path

import structlog

from capture.base import BaseScraper
from config import CaptureSettings

logger = structlog.get_logger(__name__)

# Known datasets in the dipMex repository with their relative paths.
DIPMEX_DATASETS: dict[str, str] = {
    "votes_64": "data/votaciones64.csv",
    "votes_65": "data/votaciones65.csv",
    "votes_66": "data/votaciones66.csv",
    "deputies_64": "data/diputados64.csv",
    "deputies_65": "data/diputados65.csv",
    "deputies_66": "data/diputados66.csv",
}


class DipMexClient(BaseScraper):
    """Download structured legislative datasets from the dipMex GitHub repository.

    The dipMex project (github.com/emagar/dipMex) compiles roll-call vote databases
    for recent Mexican legislatures. This client downloads the CSV files and stores
    them in the raw landing zone for downstream processing.
    """

    def __init__(self, settings: CaptureSettings | None = None) -> None:
        super().__init__(settings)
        self.base_url = self.settings.dipmex_repo_url

    def download_dataset(self, name: str, path: str) -> Path | None:
        """Download a single dataset file from the dipMex repository.

        Args:
            name: Human-readable dataset identifier.
            path: Relative path within the repository.

        Returns:
            Path to saved file, or None if download failed.
        """
        url = f"{self.base_url}/{path}"
        try:
            response = self.fetch(url)
            output_path = self.save_raw(
                response.text,
                f"dipmex/{name}.csv",
            )
            self.log.info("downloaded_dataset", name=name, rows_hint=response.text.count("\n"))
            return output_path
        except Exception:
            self.log.exception("download_failed", name=name, url=url)
            return None

    def scrape(self) -> list[Path]:
        """Download all known dipMex datasets.

        Returns:
            List of paths to successfully downloaded files.
        """
        self.log.info("starting_dipmex_download", datasets=list(DIPMEX_DATASETS.keys()))
        results: list[Path] = []

        for name, path in DIPMEX_DATASETS.items():
            result = self.download_dataset(name, path)
            if result is not None:
                results.append(result)
            time.sleep(self.settings.rate_limit_delay)

        self.log.info(
            "dipmex_download_complete",
            total=len(DIPMEX_DATASETS),
            successful=len(results),
        )
        return results
