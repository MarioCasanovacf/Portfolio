"""Tests for capture modules using mocked HTTP responses."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from capture.base import BaseScraper
from capture.dipmex import DipMexClient, DIPMEX_DATASETS
from config import CaptureSettings


@pytest.fixture
def tmp_output(tmp_path: Path) -> CaptureSettings:
    """Create capture settings pointing to a temporary directory."""
    return CaptureSettings(output_dir=tmp_path / "raw")


class TestBaseScraper:
    """Tests for the base scraper functionality."""

    def test_save_raw_text(self, tmp_output: CaptureSettings) -> None:
        """Text data is saved correctly to the output directory."""

        class DummyScraper(BaseScraper):
            def scrape(self) -> list[Path]:
                return []

        with DummyScraper(tmp_output) as scraper:
            path = scraper.save_raw("test,data\n1,2", "test.csv")
            assert path.exists()
            assert path.read_text() == "test,data\n1,2"

    def test_save_raw_bytes(self, tmp_output: CaptureSettings) -> None:
        """Binary data is saved correctly."""

        class DummyScraper(BaseScraper):
            def scrape(self) -> list[Path]:
                return []

        with DummyScraper(tmp_output) as scraper:
            path = scraper.save_raw(b"\x00\x01\x02", "binary.dat")
            assert path.exists()
            assert path.read_bytes() == b"\x00\x01\x02"

    def test_save_raw_creates_subdirectories(self, tmp_output: CaptureSettings) -> None:
        """Nested paths are created automatically."""

        class DummyScraper(BaseScraper):
            def scrape(self) -> list[Path]:
                return []

        with DummyScraper(tmp_output) as scraper:
            path = scraper.save_raw("data", "subdir/nested/file.csv")
            assert path.exists()


class TestDipMexClient:
    """Tests for the dipMex downloader with mocked HTTP."""

    @patch("capture.base.httpx.Client")
    def test_download_dataset_success(
        self, mock_client_cls: MagicMock, tmp_output: CaptureSettings
    ) -> None:
        """Successful download saves CSV to the correct path."""
        mock_response = MagicMock()
        mock_response.text = "col1,col2\nval1,val2\nval3,val4"
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = DipMexClient(tmp_output)
        client.client = mock_client

        path = client.download_dataset("test_ds", "data/test.csv")
        assert path is not None
        assert path.exists()
        assert "val1" in path.read_text()

    @patch("capture.base.httpx.Client")
    def test_download_dataset_failure_returns_none(
        self, mock_client_cls: MagicMock, tmp_output: CaptureSettings
    ) -> None:
        """Failed download returns None without raising."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client_cls.return_value = mock_client

        client = DipMexClient(tmp_output)
        client.client = mock_client

        path = client.download_dataset("test_ds", "data/test.csv")
        assert path is None

    def test_dipmex_datasets_defined(self) -> None:
        """Verify all expected datasets are configured."""
        assert len(DIPMEX_DATASETS) >= 4
        assert all(path.endswith(".csv") for path in DIPMEX_DATASETS.values())
