"""Tests for Pydantic domain models."""

from datetime import date

import pytest

from models.legislative import Deputy, VoteRecord, VoteSummary


class TestDeputy:
    """Tests for the Deputy model."""

    def test_valid_deputy(self) -> None:
        deputy = Deputy(
            legislature=65,
            legislator_id="DEP001",
            full_name="María López Hernández",
            party="morena",
            state="ciudad de méxico",
            district_type="MR",
            gender="F",
        )
        assert deputy.party == "MORENA"
        assert deputy.state == "Ciudad De México"

    def test_invalid_legislature_too_low(self) -> None:
        with pytest.raises(ValueError):
            Deputy(
                legislature=50,
                legislator_id="DEP001",
                full_name="Test Name",
                party="PAN",
                state="Jalisco",
            )

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError):
            Deputy(
                legislature=65,
                legislator_id="DEP001",
                full_name="X",
                party="PAN",
                state="Jalisco",
            )


class TestVoteRecord:
    """Tests for the VoteRecord model."""

    def test_spanish_vote_normalization(self) -> None:
        record = VoteRecord(
            legislature=65,
            vote_id="V001",
            legislator_name="Test Legislator",
            party="PAN",
            vote_cast="A favor",
        )
        assert record.vote_cast == "FOR"

    def test_against_vote(self) -> None:
        record = VoteRecord(
            legislature=65,
            vote_id="V001",
            legislator_name="Test Legislator",
            party="PRI",
            vote_cast="en contra",
        )
        assert record.vote_cast == "AGAINST"

    def test_absent_vote(self) -> None:
        record = VoteRecord(
            legislature=66,
            vote_id="V002",
            legislator_name="Test Legislator",
            party="MORENA",
            vote_cast="ausente",
        )
        assert record.vote_cast == "ABSENT"

    def test_invalid_vote_cast_passthrough(self) -> None:
        """Unknown vote values pass through uppercased but are caught by Literal validation."""
        with pytest.raises(ValueError):
            VoteRecord(
                legislature=65,
                vote_id="V001",
                legislator_name="Test Legislator",
                party="PAN",
                vote_cast="maybe",
            )


class TestVoteSummary:
    """Tests for the VoteSummary model."""

    def test_computed_properties(self) -> None:
        summary = VoteSummary(
            legislature=65,
            vote_id="V001",
            votes_for=300,
            votes_against=150,
            abstentions=10,
            absences=40,
        )
        assert summary.total_present == 460
        assert summary.total_eligible == 500
        assert summary.approval_rate == pytest.approx(300 / 460)
        assert summary.is_approved is True

    def test_rejected_vote(self) -> None:
        summary = VoteSummary(
            legislature=65,
            vote_id="V002",
            votes_for=100,
            votes_against=350,
            abstentions=10,
        )
        assert summary.is_approved is False

    def test_zero_present(self) -> None:
        summary = VoteSummary(
            legislature=65,
            vote_id="V003",
            votes_for=0,
            votes_against=0,
            absences=500,
        )
        assert summary.approval_rate is None
        assert summary.is_approved is False
