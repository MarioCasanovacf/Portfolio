"""Unit tests for ``quantitative_finance.config``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quantitative_finance.config import Settings, get_settings


@pytest.mark.unit
def test_default_settings_load() -> None:
    s = Settings()
    assert s.random_seed == 42
    assert s.lob_n_events > 0
    assert s.assets_n >= 2
    assert s.assets_n_days >= 2


@pytest.mark.unit
def test_get_settings_returns_fresh_instance() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is not s2
    assert s1.model_dump() == s2.model_dump()


@pytest.mark.unit
def test_invalid_lob_n_events_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(lob_n_events=0)


@pytest.mark.unit
def test_invalid_lob_start_price_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(lob_start_price=-1.0)


@pytest.mark.unit
def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QFINANCE_RANDOM_SEED", "123")
    s = Settings()
    assert s.random_seed == 123
