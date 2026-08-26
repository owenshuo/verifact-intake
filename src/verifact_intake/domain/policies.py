from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from verifact_intake.domain.models import (
    Assertion,
    AssertionStatus,
    ConflictRecord,
)


def _canonical_value(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class IntakeAssessment:
    assertions: tuple[Assertion, ...]
    conflicts: tuple[ConflictRecord, ...]


class TrustPolicy:
    """Small, deterministic policy used by the hackathon intake slice."""

    def __init__(self, *, auto_accept_confidence: float = 0.98, auto_accept_authority: int = 90):
        self.auto_accept_confidence = auto_accept_confidence
        self.auto_accept_authority = auto_accept_authority

    def assess(self, assertions: Iterable[Assertion]) -> IntakeAssessment:
        grouped: dict[str, list[Assertion]] = defaultdict(list)
        materialized = list(assertions)
        for assertion in materialized:
            grouped[assertion.fact_key].append(assertion)

        conflict_ids: set[object] = set()
        conflicts: list[ConflictRecord] = []
        for fact_key, candidates in grouped.items():
            distinct_values = {_canonical_value(candidate.value) for candidate in candidates}
            if len(distinct_values) <= 1:
                continue
            ids = tuple(candidate.id for candidate in candidates)
            conflict_ids.update(ids)
            conflicts.append(
                ConflictRecord(
                    fact_key=fact_key,
                    assertion_ids=ids,
                    reason="Sources provide incompatible values for the same normalized fact key.",
                )
            )

        assessed: list[Assertion] = []
        for assertion in materialized:
            if assertion.id in conflict_ids:
                status = AssertionStatus.CONFLICTED
            elif (
                assertion.confidence >= self.auto_accept_confidence
                and assertion.authority >= self.auto_accept_authority
            ):
                status = AssertionStatus.ACCEPTED
            else:
                status = AssertionStatus.REVIEW_REQUIRED
            assessed.append(assertion.model_copy(update={"status": status}))

        return IntakeAssessment(assertions=tuple(assessed), conflicts=tuple(conflicts))
