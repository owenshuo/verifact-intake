from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from verifact_intake.domain.audit import AuditEvent
from verifact_intake.domain.models import (
    Assertion,
    ConflictRecord,
    EffectiveFact,
    FrozenModel,
    ReviewDecision,
    SourceArtifact,
    utc_now,
)


class IntakeRun(FrozenModel):
    id: UUID = Field(default_factory=uuid4)
    dataset: str = Field(min_length=1, max_length=200)
    extraction_provider: str = Field(min_length=1, max_length=100)
    artifacts: tuple[SourceArtifact, ...]
    assertions: tuple[Assertion, ...]
    conflicts: tuple[ConflictRecord, ...]
    reviews: tuple[ReviewDecision, ...] = ()
    facts: tuple[EffectiveFact, ...] = ()
    audit_events: tuple[AuditEvent, ...] = ()
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def open_review_count(self) -> int:
        reviewed_ids = {decision.assertion_id for decision in self.reviews}
        return len(
            {
                assertion.fact_key
                for assertion in self.assertions
                if assertion.status.value in {"review_required", "conflicted"}
                and assertion.id not in reviewed_ids
            }
        )
