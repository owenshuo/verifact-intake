from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from verifact_intake.application.compiler import AssertionCompiler, load_golden_dataset
from verifact_intake.domain.audit import AuditEventType, append_audit_event
from verifact_intake.domain.models import (
    Assertion,
    AssertionStatus,
    ConflictStatus,
    ReviewDecision,
    ReviewOutcome,
    SourceArtifact,
    SourceKind,
)
from verifact_intake.domain.policies import TrustPolicy
from verifact_intake.domain.promotion import PromotionPolicy
from verifact_intake.domain.run import IntakeRun
from verifact_intake.ports.document_extractor import DocumentExtractor, ExtractedDocument
from verifact_intake.ports.repository import RunRepository


class RunNotFoundError(LookupError):
    pass


class InvalidReviewError(ValueError):
    pass


SOURCE_KINDS = {
    "atlas-api-reference.pdf": SourceKind.API_REFERENCE,
    "atlas-operations-guide.pdf": SourceKind.BUSINESS_GUIDE,
    "atlas-quality-policy.pdf": SourceKind.QUALITY_POLICY,
}


class IntakeService:
    def __init__(
        self,
        *,
        extractor: DocumentExtractor,
        repository: RunRepository,
        trust_policy: TrustPolicy | None = None,
        promotion_policy: PromotionPolicy | None = None,
    ) -> None:
        self._extractor = extractor
        self._repository = repository
        self._trust_policy = trust_policy or TrustPolicy()
        self._promotion_policy = promotion_policy or PromotionPolicy()
        self._compiler = AssertionCompiler()

    async def create_run(self, *, pdf_dir: Path, golden_path: Path) -> IntakeRun:
        dataset = load_golden_dataset(golden_path)
        filenames = sorted({rule.source for rule in dataset.assertions})
        artifacts: list[SourceArtifact] = []
        documents: dict[str, ExtractedDocument] = {}

        for filename in filenames:
            path = pdf_dir / filename
            document = await self._extractor.extract(path)
            documents[filename] = document
            artifacts.append(
                SourceArtifact(
                    filename=filename,
                    media_type="application/pdf",
                    source_kind=SOURCE_KINDS.get(filename, SourceKind.OTHER),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    extraction_provider=document.provider,
                )
            )

        assertions = self._compiler.compile(dataset, tuple(artifacts), documents)
        assessment = self._trust_policy.assess(assertions)
        promotion = self._promotion_policy.promote(assessment.assertions, ())
        provider_names = sorted({document.provider for document in documents.values()})
        run = IntakeRun(
            dataset=dataset.dataset,
            extraction_provider=", ".join(provider_names),
            artifacts=tuple(artifacts),
            assertions=assessment.assertions,
            conflicts=assessment.conflicts,
            facts=promotion.new_facts,
        )
        events = append_audit_event(
            run.audit_events,
            event_type=AuditEventType.INTAKE_COMPLETED,
            payload={
                "run_id": str(run.id),
                "dataset": run.dataset,
                "provider": run.extraction_provider,
                "artifact_count": len(run.artifacts),
                "assertion_count": len(run.assertions),
                "conflict_count": len(run.conflicts),
            },
        )
        for fact in promotion.new_facts:
            events = append_audit_event(
                events,
                event_type=AuditEventType.FACT_PROMOTED,
                payload=self._fact_payload(fact.fact_key, fact.version, fact.assertion_ids),
            )
        run = run.model_copy(update={"audit_events": events})
        self._repository.save(run)
        return run

    def get_run(self, run_id: UUID) -> IntakeRun:
        run = self._repository.get(run_id)
        if run is None:
            raise RunNotFoundError(str(run_id))
        return run

    def list_runs(self) -> tuple[IntakeRun, ...]:
        return self._repository.list()

    def resolve(
        self,
        *,
        run_id: UUID,
        chosen_assertion_id: UUID,
        reviewer: str,
        rationale: str,
        corrected_value: object | None = None,
    ) -> IntakeRun:
        run = self.get_run(run_id)
        chosen = next(
            (item for item in run.assertions if item.id == chosen_assertion_id), None
        )
        if chosen is None:
            raise InvalidReviewError("The chosen assertion does not belong to this run")
        if chosen.status not in {
            AssertionStatus.CONFLICTED,
            AssertionStatus.REVIEW_REQUIRED,
        }:
            raise InvalidReviewError(
                "Only conflicted or review-required assertions can be reviewed"
            )

        candidates = [item for item in run.assertions if item.fact_key == chosen.fact_key]
        decisions = tuple(
            self._decision_for_candidate(
                candidate,
                chosen=chosen,
                reviewer=reviewer,
                rationale=rationale,
                corrected_value=corrected_value,
            )
            for candidate in candidates
        )
        reviews = (*run.reviews, *decisions)
        promotion = self._promotion_policy.promote(run.assertions, reviews, run.facts)
        resolved_conflicts = tuple(
            conflict.model_copy(update={"status": ConflictStatus.RESOLVED})
            if conflict.fact_key == chosen.fact_key
            else conflict
            for conflict in run.conflicts
        )
        events = run.audit_events
        for decision in decisions:
            events = append_audit_event(
                events,
                event_type=AuditEventType.REVIEW_RECORDED,
                payload={
                    "decision_id": str(decision.id),
                    "assertion_id": str(decision.assertion_id),
                    "fact_key": chosen.fact_key,
                    "outcome": decision.outcome.value,
                    "reviewer": decision.reviewer,
                },
            )
        for fact in promotion.new_facts:
            events = append_audit_event(
                events,
                event_type=AuditEventType.FACT_PROMOTED,
                payload=self._fact_payload(fact.fact_key, fact.version, fact.assertion_ids),
            )
        updated = run.model_copy(
            update={
                "reviews": reviews,
                "facts": (*run.facts, *promotion.new_facts),
                "conflicts": resolved_conflicts,
                "audit_events": events,
            }
        )
        self._repository.save(updated)
        return updated

    @staticmethod
    def _decision_for_candidate(
        candidate: Assertion,
        *,
        chosen: Assertion,
        reviewer: str,
        rationale: str,
        corrected_value: object | None,
    ) -> ReviewDecision:
        if candidate.id != chosen.id:
            outcome = ReviewOutcome.REJECT
            correction = None
        elif corrected_value is not None:
            outcome = ReviewOutcome.CORRECT
            correction = corrected_value
        else:
            outcome = ReviewOutcome.APPROVE
            correction = None
        return ReviewDecision(
            assertion_id=candidate.id,
            assertion_fingerprint=candidate.fingerprint,
            outcome=outcome,
            reviewer=reviewer,
            rationale=rationale,
            corrected_value=correction,
        )

    @staticmethod
    def _fact_payload(
        fact_key: str, version: int, assertion_ids: tuple[UUID, ...]
    ) -> dict[str, object]:
        return {
            "fact_key": fact_key,
            "version": version,
            "assertion_ids": [str(item) for item in assertion_ids],
        }
