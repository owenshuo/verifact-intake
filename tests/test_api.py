from pathlib import Path

import httpx
import pytest

from verifact_intake.adapters.fixture import FixtureDocumentExtractor
from verifact_intake.adapters.sqlite_repository import SQLiteRunRepository
from verifact_intake.api import app, get_service
from verifact_intake.application.service import IntakeService

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_api_exposes_intake_review_and_evidence_export(tmp_path: Path) -> None:
    service = IntakeService(
        extractor=FixtureDocumentExtractor(ROOT / "data" / "synthetic" / "fixtures"),
        repository=SQLiteRunRepository(tmp_path / "api.db"),
    )
    app.dependency_overrides[get_service] = lambda: service
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            page_response = await client.get("/")
            assert page_response.status_code == 200
            assert "Documents become facts" in page_response.text

            create_response = await client.post("/api/demo/runs")
            assert create_response.status_code == 201
            run = create_response.json()
            assert len(run["assertions"]) == 12
            assert len(run["conflicts"]) == 3

            export_response = await client.get(f"/api/runs/{run['id']}/export")
            export = export_response.json()
            assert export_response.status_code == 200
            assert export["schema"] == "verifact.ontology-export/v1"
            assert len(export["facts"]) == 5
            assert export["audit"]["verified"] is True
            assert all(fact["evidence"] for fact in export["facts"])

            chosen = next(
                assertion
                for assertion in run["assertions"]
                if assertion["subject_id"] == "operation:create-change"
                and assertion["predicate"] == "http.method"
                and assertion["value"] == "POST"
            )
            review_response = await client.post(
                f"/api/runs/{run['id']}/reviews",
                json={
                    "chosen_assertion_id": chosen["id"],
                    "reviewer": "api-reviewer",
                    "rationale": "The versioned API reference is normative.",
                },
            )
            assert review_response.status_code == 200
            assert len(review_response.json()["facts"]) == 6
    finally:
        app.dependency_overrides.clear()
