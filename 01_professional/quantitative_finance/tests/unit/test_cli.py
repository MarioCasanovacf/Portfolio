"""Smoke tests for the ``qfinance`` CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantitative_finance.cli import main


@pytest.mark.integration
def test_cli_generate_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QFINANCE_LOB_N_EVENTS", "50")
    monkeypatch.setenv("QFINANCE_ASSETS_N", "3")
    monkeypatch.setenv("QFINANCE_ASSETS_N_DAYS", "20")
    monkeypatch.setenv("QFINANCE_HIGH_VOL_START", "5")
    monkeypatch.setenv("QFINANCE_HIGH_VOL_END", "10")
    monkeypatch.setenv("QFINANCE_MEDIUM_VOL_START", "12")
    monkeypatch.setenv("QFINANCE_MEDIUM_VOL_END", "15")

    rc = main(["generate-data", "--all", "--out-dir", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "lob_events_synthetic.csv").exists()
    assert (tmp_path / "correlated_assets_synthetic.csv").exists()


@pytest.mark.unit
def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "qfinance" in capsys.readouterr().out
