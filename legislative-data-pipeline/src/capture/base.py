"""Base scraper with retry logic, rate limiting, and structured logging."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import CaptureSettings, get_settings

logger = structlog.get_logger(__name__)


class BaseScraper(ABC):
    """Abstract base for all legislative data scrapers.

    Provides HTTP client with retry logic, rate limiting, and structured logging.
    Subclasses implement `scrape()` to define source-specific extraction logic.
    """

    def __init__(self, settings: CaptureSettings | None = None) -> None:
        self.settings = settings or get_settings().capture
        self.settings.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            timeout=self.settings.request_timeout,
            headers={"User-Agent": self.settings.user_agent},
            follow_redirects=True,
        )
        self.log = logger.bind(scraper=self.__class__.__name__)

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "BaseScraper":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=30),
        reraise=True,
    )
    def fetch(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """Fetch a URL with automatic retries and exponential backoff.

        Args:
            url: Target URL.
            params: Optional query parameters.

        Returns:
            HTTP response object.

        Raises:
            httpx.HTTPStatusError: After exhausting retries on 4xx/5xx responses.
            httpx.ConnectError: After exhausting retries on connection failures.
        """
        self.log.info("fetching_url", url=url, params=params)
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response

    def save_raw(self, data: bytes | str, filename: str) -> Path:
        """Persist raw data to the landing zone.

        Args:
            data: Raw content (bytes or string).
            filename: Output filename within the scraper's output directory.

        Returns:
            Path to the saved file.
        """
        output_path = self.settings.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, str):
            output_path.write_text(data, encoding="utf-8")
        else:
            output_path.write_bytes(data)

        self.log.info("saved_raw_file", path=str(output_path), size=output_path.stat().st_size)
        return output_path

    @abstractmethod
    def scrape(self) -> list[Path]:
        """Execute the scraping logic for this source.

        Returns:
            List of paths to saved raw files.
        """
        ...
