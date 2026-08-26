from uuid import uuid4

from verifact_intake.domain.models import Assertion, AssertionStatus, EvidenceLocator
from verifact_intake.domain.policies import TrustPolicy


def make_assertion(*, value: object, confidence: float = 0.99, authority: int = 95) -> Assertion:
    return Assertion(
        subject_id="operation:create-change",
        predicate="http.method",
        value=value,
        confidence=confidence,
        authority=authority,
        evidence=(
            EvidenceLocator(
                artifact_id=uuid4(),
                page=1,
                quote=f"Method is {value}.",
            ),
        ),
    )


def test_high_confidence_authoritative_assertion_is_accepted() -> None:
    result = TrustPolicy().assess([make_assertion(value="POST")])

    assert result.assertions[0].status is AssertionStatus.ACCEPTED
    assert result.conflicts == ()


def test_low_confidence_assertion_requires_review() -> None:
    result = TrustPolicy().assess([make_assertion(value="POST", confidence=0.72)])

    assert result.assertions[0].status is AssertionStatus.REVIEW_REQUIRED


def test_incompatible_values_create_conflict_and_block_auto_acceptance() -> None:
    result = TrustPolicy().assess(
        [make_assertion(value="POST"), make_assertion(value="PUT")]
    )

    assert len(result.conflicts) == 1
    assert {item.status for item in result.assertions} == {AssertionStatus.CONFLICTED}

