"""Smoke tests for ``data_fetcher`` (no network)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import data_fetcher


@pytest.mark.unit
def test_fetch_pdb_callable() -> None:
    assert callable(data_fetcher.fetch_pdb)


@pytest.mark.unit
def test_fetch_pdb_writes_expected_path(tmp_path: Path) -> None:
    expected = tmp_path / "1xyz.pdb"

    def fake_retrieve(url: str, dest: str) -> None:
        Path(dest).write_text("HEADER  fake pdb\nEND\n")

    with patch.object(data_fetcher.urllib.request, "urlretrieve", side_effect=fake_retrieve):
        result = data_fetcher.fetch_pdb("1XYZ", output_dir=str(tmp_path))

    assert result == str(expected)
    assert expected.exists()
    assert "HEADER" in expected.read_text()


@pytest.mark.unit
def test_fetch_pdb_returns_none_on_error(tmp_path: Path) -> None:
    with patch.object(data_fetcher.urllib.request, "urlretrieve", side_effect=OSError("boom")):
        result = data_fetcher.fetch_pdb("9zzz", output_dir=str(tmp_path))
    assert result is None
