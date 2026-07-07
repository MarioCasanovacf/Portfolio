"""Domain models for Mexican legislative data.

Pydantic models enforce data contracts between pipeline stages.
The capture layer produces raw data; these models validate it before
loading into the warehouse.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Deputy(BaseModel):
    """A legislator (diputado/a) in the Mexican Chamber of Deputies."""

    legislature: int = Field(ge=60, le=70, description="Legislature number")
    legislator_id: str = Field(min_length=1, description="Unique identifier from source")
    full_name: str = Field(min_length=2)
    party: str = Field(min_length=1, description="Party abbreviation (e.g., MORENA, PAN)")
    state: str = Field(min_length=1, description="Entidad federativa")
    district_type: Literal["MR", "RP"] | None = None
    district_number: str | None = None
    gender: Literal["M", "F"] | None = None

    @field_validator("party")
    @classmethod
    def normalize_party(cls, v: str) -> str:
        """Normalize party abbreviation to uppercase."""
        return v.strip().upper()

    @field_validator("state")
    @classmethod
    def normalize_state(cls, v: str) -> str:
        """Normalize state name: title case, stripped."""
        return v.strip().title()


class VoteRecord(BaseModel):
    """An individual legislator's vote on a specific matter."""

    legislature: int = Field(ge=60, le=70)
    vote_date: date | None = None
    vote_id: str = Field(min_length=1)
    legislator_name: str = Field(min_length=2)
    party: str
    vote_cast: Literal["FOR", "AGAINST", "ABSTAIN", "ABSENT"]

    @field_validator("vote_cast", mode="before")
    @classmethod
    def normalize_vote_cast(cls, v: str) -> str:
        """Map Spanish vote values to standardized English equivalents."""
        mapping = {
            "FAVOR": "FOR",
            "A FAVOR": "FOR",
            "CONTRA": "AGAINST",
            "EN CONTRA": "AGAINST",
            "ABSTENCIÓN": "ABSTAIN",
            "ABSTENCION": "ABSTAIN",
            "AUSENTE": "ABSENT",
        }
        normalized = v.strip().upper()
        return mapping.get(normalized, normalized)


class VoteSummary(BaseModel):
    """Aggregate vote outcome for a single vote event."""

    legislature: int = Field(ge=60, le=70)
    session_date: date | None = None
    vote_id: str = Field(min_length=1)
    description: str = ""
    votes_for: int = Field(ge=0)
    votes_against: int = Field(ge=0)
    abstentions: int = Field(ge=0, default=0)
    absences: int = Field(ge=0, default=0)
    detail_url: str = ""

    @property
    def total_present(self) -> int:
        """Total legislators who voted (excludes absences)."""
        return self.votes_for + self.votes_against + self.abstentions

    @property
    def total_eligible(self) -> int:
        """Total legislators expected to vote."""
        return self.total_present + self.absences

    @property
    def approval_rate(self) -> float | None:
        """Fraction of present votes that were in favor."""
        if self.total_present == 0:
            return None
        return self.votes_for / self.total_present

    @property
    def is_approved(self) -> bool:
        """Whether the vote passed with simple majority."""
        rate = self.approval_rate
        return rate is not None and rate > 0.5


class CaptureMetadata(BaseModel):
    """Metadata attached to every captured file for lineage tracking."""

    source: str = Field(description="Source identifier (e.g., 'dipmex', 'diputados')")
    captured_at: datetime = Field(default_factory=datetime.now)
    file_path: str
    record_count: int = Field(ge=0)
    checksum: str = Field(default="", description="MD5 hash of file content")
