from uuid import uuid4

import pytest
from pydantic import ValidationError

from verifact_intake.domain.models import (
    Assertion,
    EvidenceLocator,
    ReviewDecision,
    ReviewOutcome,
)


def _assertion(value: object = "POST") -> Assertion:
    return Assertion(
        subject_id="operation:create-change",
        predicate="http.method",
        value=value,
        confidence=0.99,
        authority=95,
        evidence=(
            EvidenceLocator(
                artifact_id=uuid4(),
                page=1,
                quote="Create a change request with POST /changes.",
            ),
        ),
    )


def test_assertion_fingerprint_is_stable() -> None:
    assertion = _assertion()
    copy = assertion.model_copy(update={"id": uuid4()})

    assert assertion.fingerprint == copy.fingerprint


def test_correction_requires_corrected_value() -> None:
    assertion = _assertion()

    with pytest.raises(ValidationError):
        ReviewDecision(
            assertion_id=assertion.id,
            assertion_fingerprint=assertion.fingerprint,
            outcome=ReviewOutcome.CORRECT,
            reviewer="demo-reviewer",
            rationale="The source contains a typo.",
        )

