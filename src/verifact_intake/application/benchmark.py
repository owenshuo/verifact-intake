from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from verifact_intake.application.compiler import AssertionCompiler, load_assertion_profile
from verifact_intake.domain.models import (
    Assertion,
    AssertionStatus,
    FrozenModel,
    ReviewDecision,
    ReviewOutcome,
    SourceArtifact,
)
from verifact_intake.domain.policies import TrustPolicy
from verifact_intake.domain.promotion import PromotionPolicy
from verifact_intake.ports.document_extractor import ExtractedDocument


class ConfidenceBaselineMetrics(FrozenModel):
    conflict_choices: int = Field(ge=0)
    unsafe_conflict_choices: int = Field(ge=0)
    wrong_conflict_values: int = Field(ge=0)
    wrong_conflict_value_rate: float = Field(ge=0, le=1)


class VeriFactBenchmarkMetrics(FrozenModel):
    expected_conflicts: int = Field(ge=0)
    detected_conflicts: int = Field(ge=0)
    conflict_recall: float = Field(ge=0, le=1)
    unsafe_auto_promotions: int = Field(ge=0)
    safe_auto_promotions: int = Field(ge=0)
    human_review_tasks: int = Field(ge=0)
    final_fact_accuracy: float = Field(ge=0, le=1)
    evidence_coverage: float = Field(ge=0, le=1)


class TrustBenchmarkReport(FrozenModel):
    schema_name: str = Field(alias="schema")
    cases: int = Field(ge=1)
    description: str
    confidence_baseline: ConfidenceBaselineMetrics
    verifact: VeriFactBenchmarkMetrics


_METHOD_VARIANTS = ("PUT", "PATCH", "DELETE", "GET", "MERGE")
_APPROVAL_VARIANTS = ("one", "three", "four", "five")
_RETENTION_VARIANTS = (30, 60, 90, 120, 365)
_NORMATIVE_CONFIDENCES = (0.99, 0.94, 0.89)


def run_synthetic_trust_benchmark(
    *,
    profile_path: Path,
    fixture_dir: Path,
    pdf_dir: Path,
    golden_path: Path,
    case_count: int = 30,
) -> TrustBenchmarkReport:
    if case_count < 1:
        raise ValueError("case_count must be at least 1")

    profile = load_assertion_profile(profile_path)
    documents = _load_documents(profile.sources, fixture_dir)
    artifacts = tuple(
        SourceArtifact(
            filename=source.filename,
            media_type="application/pdf",
            source_kind=source.source_kind,
            sha256=hashlib.sha256((pdf_dir / source.filename).read_bytes()).hexdigest(),
            extraction_provider="benchmark-fixture",
        )
        for source in profile.sources
    )
    expected_values, expected_conflict_keys = _load_expected_values(golden_path)

    expected_conflicts = 0
    detected_conflicts = 0
    unsafe_baseline_choices = 0
    wrong_baseline_values = 0
    unsafe_auto_promotions = 0
    safe_auto_promotions = 0
    human_review_tasks = 0
    correct_final_facts = 0
    expected_final_facts = 0
    facts_with_evidence = 0
    total_final_facts = 0

    compiler = AssertionCompiler()
    trust_policy = TrustPolicy()
    promotion_policy = PromotionPolicy()

    for index in range(case_count):
        variant = _variant_documents(documents, index)
        assertions = compiler.compile(profile, artifacts, variant)
        assessment = trust_policy.assess(assertions)
        detected_keys = {conflict.fact_key for conflict in assessment.conflicts}
        expected_conflicts += len(expected_conflict_keys)
        detected_conflicts += len(detected_keys & expected_conflict_keys)

        grouped = _group_assertions(assessment.assertions)
        for fact_key in expected_conflict_keys:
            candidates = grouped[fact_key]
            chosen = max(candidates, key=lambda item: (item.confidence, item.authority))
            unsafe_baseline_choices += 1
            if chosen.value != expected_values[fact_key]:
                wrong_baseline_values += 1

        automatic = promotion_policy.promote(assessment.assertions, ())
        safe_auto_promotions += len(automatic.new_facts)
        unsafe_auto_promotions += sum(
            fact.fact_key in expected_conflict_keys for fact in automatic.new_facts
        )

        review_fact_keys = {
            assertion.fact_key
            for assertion in assessment.assertions
            if assertion.status in {AssertionStatus.CONFLICTED, AssertionStatus.REVIEW_REQUIRED}
        }
        human_review_tasks += len(review_fact_keys)
        reviews = _build_reviews(grouped, review_fact_keys, expected_values)
        final = promotion_policy.promote(assessment.assertions, reviews)
        final_values = {fact.fact_key: fact.value for fact in final.new_facts}
        expected_final_facts += len(expected_values)
        correct_final_facts += sum(
            final_values.get(fact_key) == value for fact_key, value in expected_values.items()
        )
        assertion_by_id = {assertion.id: assertion for assertion in assessment.assertions}
        total_final_facts += len(final.new_facts)
        facts_with_evidence += sum(
            all(assertion_by_id[item].evidence for item in fact.assertion_ids)
            for fact in final.new_facts
        )

    conflict_recall = detected_conflicts / expected_conflicts if expected_conflicts else 1.0
    wrong_rate = wrong_baseline_values / unsafe_baseline_choices if unsafe_baseline_choices else 0.0
    final_accuracy = correct_final_facts / expected_final_facts if expected_final_facts else 1.0
    evidence_coverage = facts_with_evidence / total_final_facts if total_final_facts else 1.0
    return TrustBenchmarkReport(
        schema="verifact.trust-benchmark/v1",
        cases=case_count,
        description=(
            "Deterministic evidence variations compare a confidence-only selector with "
            "VeriFact conflict, review, and promotion gates."
        ),
        confidence_baseline=ConfidenceBaselineMetrics(
            conflict_choices=unsafe_baseline_choices,
            unsafe_conflict_choices=unsafe_baseline_choices,
            wrong_conflict_values=wrong_baseline_values,
            wrong_conflict_value_rate=wrong_rate,
        ),
        verifact=VeriFactBenchmarkMetrics(
            expected_conflicts=expected_conflicts,
            detected_conflicts=detected_conflicts,
            conflict_recall=conflict_recall,
            unsafe_auto_promotions=unsafe_auto_promotions,
            safe_auto_promotions=safe_auto_promotions,
            human_review_tasks=human_review_tasks,
            final_fact_accuracy=final_accuracy,
            evidence_coverage=evidence_coverage,
        ),
    )


def _load_documents(
    sources: tuple[Any, ...], fixture_dir: Path
) -> dict[str, ExtractedDocument]:
    documents: dict[str, ExtractedDocument] = {}
    for source in sources:
        payload = cast(
            dict[str, Any],
            json.loads(
                (fixture_dir / f"{Path(source.filename).stem}.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        documents[source.filename] = ExtractedDocument.model_validate(payload)
    return documents


def _load_expected_values(golden_path: Path) -> tuple[dict[str, Any], set[str]]:
    payload = cast(
        dict[str, Any], json.loads(golden_path.read_text(encoding="utf-8"))
    )
    assertion_rows = cast(list[dict[str, Any]], payload["assertions"])
    expected_values: dict[str, Any] = {}
    expected_conflict_keys: set[str] = set()
    for row in assertion_rows:
        fact_key = f"{row['subject_id']}::{row['predicate']}"
        if row["expected_status"] == "accepted":
            expected_values[fact_key] = row["value"]
        elif row["expected_status"] == "conflicted":
            expected_conflict_keys.add(fact_key)
    expected_values.update(
        cast(dict[str, Any], payload["expected_effective_facts_after_review"])
    )
    return expected_values, expected_conflict_keys


def _variant_documents(
    documents: dict[str, ExtractedDocument], index: int
) -> dict[str, ExtractedDocument]:
    normative_confidence = _NORMATIVE_CONFIDENCES[index % len(_NORMATIVE_CONFIDENCES)]
    method = _METHOD_VARIANTS[index % len(_METHOD_VARIANTS)]
    approval = _APPROVAL_VARIANTS[index % len(_APPROVAL_VARIANTS)]
    retention = _RETENTION_VARIANTS[index % len(_RETENTION_VARIANTS)]

    api_document = _replace_blocks(
        documents["atlas-api-reference.pdf"],
        {
            "api-create": {
                "confidence": normative_confidence,
            }
        },
    )
    operations_document = _replace_blocks(
        documents["atlas-operations-guide.pdf"],
        {
            "ops-create": {
                "text": f"The legacy guide describes {method} as the create-change HTTP method.",
                "confidence": 0.97,
            },
            "ops-approval": {
                "text": (
                    f"{approval.title()} duty manager approvals are sufficient before a "
                    "high-risk change is scheduled."
                ),
                "confidence": 0.97,
            },
            "ops-retention": {
                "text": (
                    f"Execution evidence is retained for {retention} days after the change "
                    "completes."
                ),
                "confidence": 0.97,
            },
        },
    )
    quality_document = _replace_blocks(
        documents["atlas-quality-policy.pdf"],
        {
            "policy-approval": {"confidence": normative_confidence},
            "policy-retention": {"confidence": normative_confidence},
        },
    )
    return {
        "atlas-api-reference.pdf": api_document,
        "atlas-operations-guide.pdf": operations_document,
        "atlas-quality-policy.pdf": quality_document,
    }


def _replace_blocks(
    document: ExtractedDocument, updates: dict[str, dict[str, object]]
) -> ExtractedDocument:
    blocks = tuple(
        block.model_copy(update=updates.get(block.block_id, {})) for block in document.blocks
    )
    return document.model_copy(update={"blocks": blocks})


def _group_assertions(assertions: tuple[Assertion, ...]) -> dict[str, list[Assertion]]:
    grouped: dict[str, list[Assertion]] = defaultdict(list)
    for assertion in assertions:
        grouped[assertion.fact_key].append(assertion)
    return grouped


def _build_reviews(
    grouped: dict[str, list[Assertion]],
    review_fact_keys: set[str],
    expected_values: dict[str, Any],
) -> tuple[ReviewDecision, ...]:
    reviews: list[ReviewDecision] = []
    for fact_key in sorted(review_fact_keys):
        expected = expected_values[fact_key]
        winners = [candidate for candidate in grouped[fact_key] if candidate.value == expected]
        if len(winners) != 1:
            raise ValueError(f"Benchmark case has no unique expected assertion for {fact_key}")
        winner = winners[0]
        for candidate in grouped[fact_key]:
            reviews.append(
                ReviewDecision(
                    assertion_id=candidate.id,
                    assertion_fingerprint=candidate.fingerprint,
                    outcome=(
                        ReviewOutcome.APPROVE
                        if candidate.id == winner.id
                        else ReviewOutcome.REJECT
                    ),
                    reviewer="benchmark-reviewer",
                    rationale="Selected the benchmark's normative evidence.",
                )
            )
    return tuple(reviews)
