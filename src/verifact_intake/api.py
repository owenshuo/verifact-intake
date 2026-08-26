from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from verifact_intake import __version__
from verifact_intake.adapters.fixture import FixtureDocumentExtractor
from verifact_intake.adapters.nutrient import NutrientDocumentExtractor
from verifact_intake.adapters.sqlite_repository import SQLiteRunRepository
from verifact_intake.application.service import (
    IntakeService,
    InvalidReviewError,
    RunNotFoundError,
)
from verifact_intake.config import get_settings
from verifact_intake.domain.audit import verify_audit_chain
from verifact_intake.domain.run import IntakeRun
from verifact_intake.ports.document_extractor import DocumentExtractor

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC = ROOT / "data" / "synthetic"


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chosen_assertion_id: UUID
    reviewer: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=2_000)
    corrected_value: Any | None = None


class RunSummary(BaseModel):
    id: UUID
    dataset: str
    extraction_provider: str
    artifacts: int
    assertions: int
    conflicts: int
    open_reviews: int
    effective_facts: int
    audit_events: int

    @classmethod
    def from_run(cls, run: IntakeRun) -> RunSummary:
        return cls(
            id=run.id,
            dataset=run.dataset,
            extraction_provider=run.extraction_provider,
            artifacts=len(run.artifacts),
            assertions=len(run.assertions),
            conflicts=len(run.conflicts),
            open_reviews=run.open_review_count,
            effective_facts=len(run.facts),
            audit_events=len(run.audit_events),
        )


@lru_cache
def get_service() -> IntakeService:
    settings = get_settings()
    repository = SQLiteRunRepository.from_url(settings.verifact_database_url)
    extractor: DocumentExtractor
    if settings.verifact_extraction_provider == "nutrient":
        if settings.nutrient_api_key is None:
            raise RuntimeError("NUTRIENT_API_KEY is required for the nutrient provider")
        extractor = NutrientDocumentExtractor(
            api_key=settings.nutrient_api_key.get_secret_value(),
            base_url=settings.nutrient_api_base_url,
        )
    else:
        extractor = FixtureDocumentExtractor(SYNTHETIC / "fixtures")
    return IntakeService(extractor=extractor, repository=repository)


Service = Annotated[IntakeService, Depends(get_service)]

app = FastAPI(
    title="VeriFact Intake",
    version=__version__,
    description="Evidence-linked document-to-ontology intake with human review.",
)
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")
app.mount("/artifacts", StaticFiles(directory=ROOT / "output" / "pdf"), name="artifacts")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/healthz", tags=["operations"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post(
    "/api/demo/runs",
    response_model=IntakeRun,
    status_code=status.HTTP_201_CREATED,
    tags=["intake"],
)
async def create_demo_run(service: Service) -> IntakeRun:
    return await service.create_run(
        pdf_dir=ROOT / "output" / "pdf",
        golden_path=SYNTHETIC / "golden" / "assertions.json",
    )


@app.get("/api/runs", response_model=list[RunSummary], tags=["intake"])
def list_runs(service: Service) -> list[RunSummary]:
    return [RunSummary.from_run(run) for run in service.list_runs()]


@app.get("/api/runs/{run_id}", response_model=IntakeRun, tags=["intake"])
def get_run(run_id: UUID, service: Service) -> IntakeRun:
    try:
        return service.get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/runs/{run_id}/reviews", response_model=IntakeRun, tags=["review"])
def resolve_review(run_id: UUID, request: ReviewRequest, service: Service) -> IntakeRun:
    try:
        return service.resolve(
            run_id=run_id,
            chosen_assertion_id=request.chosen_assertion_id,
            reviewer=request.reviewer,
            rationale=request.rationale,
            corrected_value=request.corrected_value,
        )
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    except InvalidReviewError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/runs/{run_id}/export", tags=["export"])
def export_run(run_id: UUID, service: Service) -> dict[str, Any]:
    try:
        run = service.get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    assertions = {assertion.id: assertion for assertion in run.assertions}
    artifacts = {artifact.id: artifact for artifact in run.artifacts}
    facts: list[dict[str, Any]] = []
    for fact in run.facts:
        evidence: list[dict[str, Any]] = []
        for assertion_id in fact.assertion_ids:
            assertion = assertions[assertion_id]
            for locator in assertion.evidence:
                evidence.append(
                    {
                        "assertion_id": str(assertion.id),
                        "artifact": artifacts[locator.artifact_id].filename,
                        "page": locator.page,
                        "quote": locator.quote,
                        "block_id": locator.block_id,
                    }
                )
        facts.append(
            {
                "subject": fact.subject_id,
                "predicate": fact.predicate,
                "value": fact.value,
                "version": fact.version,
                "evidence": evidence,
            }
        )
    return {
        "schema": "verifact.ontology-export/v1",
        "run_id": str(run.id),
        "dataset": run.dataset,
        "facts": facts,
        "audit": {
            "verified": verify_audit_chain(run.audit_events),
            "event_count": len(run.audit_events),
            "head_hash": run.audit_events[-1].event_hash if run.audit_events else None,
        },
    }
