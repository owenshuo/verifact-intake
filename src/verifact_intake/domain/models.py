from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceKind(StrEnum):
    API_REFERENCE = "api_reference"
    BUSINESS_GUIDE = "business_guide"
    QUALITY_POLICY = "quality_policy"
    OTHER = "other"


class AssertionStatus(StrEnum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"
    CONFLICTED = "conflicted"
    REJECTED = "rejected"


class ConflictStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class ReviewOutcome(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    CORRECT = "correct"


class EvidenceLocator(FrozenModel):
    artifact_id: UUID
    page: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=2_000)
    block_id: str | None = None
    bounding_box: tuple[float, float, float, float] | None = None


class SourceArtifact(FrozenModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str = Field(min_length=1, max_length=255)
    media_type: str = Field(min_length=1, max_length=100)
    source_kind: SourceKind
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    extraction_provider: str = Field(min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=utc_now)


class Assertion(FrozenModel):
    id: UUID = Field(default_factory=uuid4)
    subject_id: str = Field(min_length=1, max_length=300)
    predicate: str = Field(min_length=1, max_length=200)
    value: Any
    confidence: float = Field(ge=0, le=1)
    authority: int = Field(ge=0, le=100)
    evidence: tuple[EvidenceLocator, ...] = Field(min_length=1)
    status: AssertionStatus = AssertionStatus.CANDIDATE
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def fact_key(self) -> str:
        return f"{self.subject_id}::{self.predicate}"

    @property
    def fingerprint(self) -> str:
        payload = {
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "value": self.value,
            "evidence": [item.model_dump(mode="json") for item in self.evidence],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ConflictRecord(FrozenModel):
    id: UUID = Field(default_factory=uuid4)
    fact_key: str = Field(min_length=1)
    assertion_ids: tuple[UUID, ...] = Field(min_length=2)
    reason: str = Field(min_length=1, max_length=1_000)
    status: ConflictStatus = ConflictStatus.OPEN
    created_at: datetime = Field(default_factory=utc_now)


class ReviewDecision(FrozenModel):
    id: UUID = Field(default_factory=uuid4)
    assertion_id: UUID
    assertion_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    outcome: ReviewOutcome
    reviewer: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=2_000)
    corrected_value: Any | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def correction_requires_value(self) -> ReviewDecision:
        if self.outcome is ReviewOutcome.CORRECT and self.corrected_value is None:
            raise ValueError("corrected_value is required for a correction")
        if self.outcome is not ReviewOutcome.CORRECT and self.corrected_value is not None:
            raise ValueError("corrected_value is only valid for a correction")
        return self


class EffectiveFact(FrozenModel):
    id: UUID = Field(default_factory=uuid4)
    subject_id: str = Field(min_length=1, max_length=300)
    predicate: str = Field(min_length=1, max_length=200)
    value: Any
    assertion_ids: tuple[UUID, ...] = Field(min_length=1)
    version: int = Field(ge=1)
    effective_from: datetime = Field(default_factory=utc_now)

