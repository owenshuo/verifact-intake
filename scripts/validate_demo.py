from __future__ import annotations

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from verifact_intake.adapters.fixture import FixtureDocumentExtractor
from verifact_intake.adapters.sqlite_repository import SQLiteRunRepository
from verifact_intake.application.service import IntakeService
from verifact_intake.domain.audit import verify_audit_chain

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = ROOT / "data" / "synthetic"


async def validate() -> None:
    with TemporaryDirectory() as directory:
        service = IntakeService(
            extractor=FixtureDocumentExtractor(SYNTHETIC / "fixtures"),
            repository=SQLiteRunRepository(Path(directory) / "validation.db"),
        )
        run = await service.create_run(
            pdf_dir=ROOT / "output" / "pdf",
            golden_path=SYNTHETIC / "golden" / "assertions.json",
        )
        payload = cast(
            dict[str, Any],
            json.loads(
                (SYNTHETIC / "golden" / "assertions.json").read_text(encoding="utf-8")
            ),
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
                reviewer="validation-bot",
                rationale="Golden benchmark selected the normative evidence.",
            )
        assert len(run.facts) == 8
        assert verify_audit_chain(run.audit_events)
        print(
            "Demo validation passed: "
            f"{len(run.assertions)} assertions, {len(run.conflicts)} conflicts, "
            f"{len(run.facts)} facts, {len(run.audit_events)} audit events."
        )


if __name__ == "__main__":
    asyncio.run(validate())
