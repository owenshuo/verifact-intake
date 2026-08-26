from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from verifact_intake.domain.models import FrozenModel, utc_now


class AuditEventType(StrEnum):
    INTAKE_COMPLETED = "intake_completed"
    REVIEW_RECORDED = "review_recorded"
    FACT_PROMOTED = "fact_promoted"


class AuditEvent(FrozenModel):
    sequence: int = Field(ge=1)
    event_type: AuditEventType
    payload: dict[str, Any]
    previous_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    event_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    occurred_at: datetime


def append_audit_event(
    events: tuple[AuditEvent, ...],
    *,
    event_type: AuditEventType,
    payload: dict[str, Any],
    occurred_at: datetime | None = None,
) -> tuple[AuditEvent, ...]:
    timestamp = occurred_at or utc_now()
    sequence = len(events) + 1
    previous_hash = events[-1].event_hash if events else None
    canonical = json.dumps(
        {
            "sequence": sequence,
            "event_type": event_type.value,
            "payload": payload,
            "previous_hash": previous_hash,
            "occurred_at": timestamp.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    event = AuditEvent(
        sequence=sequence,
        event_type=event_type,
        payload=payload,
        previous_hash=previous_hash,
        event_hash=event_hash,
        occurred_at=timestamp,
    )
    return (*events, event)


def verify_audit_chain(events: tuple[AuditEvent, ...]) -> bool:
    rebuilt: tuple[AuditEvent, ...] = ()
    for event in events:
        rebuilt = append_audit_event(
            rebuilt,
            event_type=event.event_type,
            payload=event.payload,
            occurred_at=event.occurred_at,
        )
        if rebuilt[-1] != event:
            return False
    return True
