from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from verifact_intake.adapters.fixture import FixtureDocumentExtractor
from verifact_intake.adapters.sqlite_repository import SQLiteRunRepository
from verifact_intake.application.agent_gate import build_agent_execution_gate
from verifact_intake.application.service import IntakeService

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = ROOT / "data" / "synthetic"


@pytest.mark.asyncio
async def test_agent_gate_blocks_until_required_facts_are_promoted(tmp_path: Path) -> None:
    service = IntakeService(
        extractor=FixtureDocumentExtractor(SYNTHETIC / "fixtures"),
        repository=SQLiteRunRepository(tmp_path / "agent-gate.db"),
    )
    run = await service.create_run(
        pdf_dir=ROOT / "output" / "pdf",
        profile_path=SYNTHETIC / "profiles" / "atlas-change-service-v1.json",
    )

    blocked = build_agent_execution_gate(run)
    assert blocked.status.value == "blocked"
    assert blocked.contract is None
    assert set(blocked.missing_fact_keys) == {
        "service:atlas-change::business.owner",
        "operation:create-change::http.method",
        "workflow:high-risk-change::approval.required_count",
        "policy:change-evidence::retention.days",
    }

    payload = cast(
        dict[str, Any],
        json.loads((SYNTHETIC / "golden" / "expected-run.json").read_text(encoding="utf-8")),
    )
    expected = cast(dict[str, Any], payload["expected_effective_facts_after_review"])
    for fact_key, value in expected.items():
        chosen = next(
            assertion
            for assertion in run.assertions
            if assertion.fact_key == fact_key and assertion.value == value
        )
        run = service.resolve(
            run_id=run.id,
            chosen_assertion_id=chosen.id,
            reviewer="agent-gate-reviewer",
            rationale="Confirmed the normative evidence before agent execution.",
        )

    ready = build_agent_execution_gate(run)
    assert ready.status.value == "ready"
    assert ready.missing_fact_keys == ()
    assert ready.invalid_fact_keys == ()
    assert ready.contract is not None
    assert ready.contract.operation == "create-change"
    assert ready.contract.service_owner == "Network Operations"
    assert ready.contract.method == "POST"
    assert ready.contract.path == "/change-api/v2/changes"
    assert ready.contract.approval_required_count == 2
    assert ready.contract.evidence_retention_days == 180
    assert ready.contract.idempotency_key_required is True
    assert ready.contract.post_change_verification_required is True
    assert len(ready.contract.evidence) == 8

    invalid_facts = tuple(
        fact.model_copy(update={"value": 0})
        if fact.fact_key == "workflow:high-risk-change::approval.required_count"
        else fact
        for fact in run.facts
    )
    invalid = build_agent_execution_gate(run.model_copy(update={"facts": invalid_facts}))
    assert invalid.status.value == "blocked"
    assert invalid.contract is None
    assert invalid.invalid_fact_keys == (
        "workflow:high-risk-change::approval.required_count",
    )
