from datetime import UTC, datetime

from verifact_intake.domain.audit import (
    AuditEventType,
    append_audit_event,
    verify_audit_chain,
)


def test_audit_chain_detects_payload_tampering() -> None:
    events = append_audit_event(
        (),
        event_type=AuditEventType.INTAKE_COMPLETED,
        payload={"assertions": 12},
        occurred_at=datetime(2026, 8, 26, tzinfo=UTC),
    )
    events = append_audit_event(
        events,
        event_type=AuditEventType.REVIEW_RECORDED,
        payload={"outcome": "approve"},
        occurred_at=datetime(2026, 8, 26, 0, 1, tzinfo=UTC),
    )

    assert verify_audit_chain(events)
    tampered = (events[0], events[1].model_copy(update={"payload": {"outcome": "reject"}}))
    assert not verify_audit_chain(tampered)
