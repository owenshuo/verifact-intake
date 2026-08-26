from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from verifact_intake.adapters.fixture import FixtureDocumentExtractor
from verifact_intake.adapters.sqlite_repository import SQLiteRunRepository
from verifact_intake.application.service import IntakeService
from verifact_intake.domain.audit import verify_audit_chain

ROOT = Path(__file__).resolve().parents[1]


def _service(database_path: Path) -> IntakeService:
    extractor = FixtureDocumentExtractor(ROOT / "data" / "synthetic" / "fixtures")
    repository = SQLiteRunRepository(database_path)
    return IntakeService(extractor=extractor, repository=repository)


@pytest.mark.asyncio
async def test_synthetic_run_builds_evidence_linked_trust_state(tmp_path: Path) -> None:
    service = _service(tmp_path / "verifact.db")

    run = await service.create_run(
        pdf_dir=ROOT / "output" / "pdf",
        golden_path=ROOT / "data" / "synthetic" / "golden" / "assertions.json",
    )

    assert run.extraction_provider == "fixture"
    assert len(run.artifacts) == 3
    assert len(run.assertions) == 12
    assert len(run.conflicts) == 3
    assert len(run.facts) == 5
    assert run.open_review_count == 4
    assert verify_audit_chain(run.audit_events)
    assert service.get_run(run.id) == run


@pytest.mark.asyncio
async def test_review_resolves_conflicts_and_promotes_expected_facts(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "verifact.db"
    service = _service(database_path)
    run = await service.create_run(
        pdf_dir=ROOT / "output" / "pdf",
        golden_path=ROOT / "data" / "synthetic" / "golden" / "assertions.json",
    )
    golden = json.loads(
        (ROOT / "data" / "synthetic" / "golden" / "assertions.json").read_text(
            encoding="utf-8"
        )
    )

    expected = golden["expected_effective_facts_after_review"]
    for fact_key, value in expected.items():
        chosen = next(
            assertion
            for assertion in run.assertions
            if assertion.fact_key == fact_key and assertion.value == value
        )
        run = service.resolve(
            run_id=run.id,
            chosen_assertion_id=chosen.id,
            reviewer="demo-reviewer",
            rationale="Selected the current normative source.",
        )

    owner = next(
        assertion
        for assertion in run.assertions
        if assertion.fact_key == "service:atlas-change::business.owner"
    )
    run = service.resolve(
        run_id=run.id,
        chosen_assertion_id=owner.id,
        reviewer="demo-reviewer",
        rationale="Business owner confirmed by operations.",
    )

    latest = {fact.fact_key: fact.value for fact in run.facts}
    assert all(latest[key] == value for key, value in expected.items())
    assert latest["service:atlas-change::business.owner"] == "Network Operations"
    assert len(run.facts) == 9
    assert run.open_review_count == 0
    assert all(conflict.status.value == "resolved" for conflict in run.conflicts)
    assert verify_audit_chain(run.audit_events)

    with (
        closing(sqlite3.connect(database_path)) as connection,
        pytest.raises(sqlite3.IntegrityError),
    ):
        connection.execute("UPDATE review_decisions SET payload_json = '{}' ")
