import json
from pathlib import Path

from verifact_intake.application.compiler import (
    AssertionCompiler,
    load_assertion_profile,
)
from verifact_intake.domain.models import SourceArtifact
from verifact_intake.domain.policies import TrustPolicy
from verifact_intake.ports.document_extractor import ExtractedBlock, ExtractedDocument

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = ROOT / "data" / "synthetic"
PROFILE_PATH = SYNTHETIC / "profiles" / "atlas-change-service-v1.json"
EXPECTED_PATH = SYNTHETIC / "golden" / "expected-run.json"


def _fixtures() -> tuple[tuple[SourceArtifact, ...], dict[str, ExtractedDocument]]:
    profile = load_assertion_profile(PROFILE_PATH)
    artifacts = tuple(
        SourceArtifact(
            filename=source.filename,
            media_type="application/pdf",
            source_kind=source.source_kind,
            sha256="0" * 64,
            extraction_provider="fixture",
        )
        for source in profile.sources
    )
    documents = {
        source.filename: ExtractedDocument.model_validate_json(
            (SYNTHETIC / "fixtures" / source.filename.replace(".pdf", ".json")).read_text(
                encoding="utf-8"
            )
        )
        for source in profile.sources
    }
    return artifacts, documents


def test_profile_derives_expected_values_and_statuses_from_fixture_blocks() -> None:
    profile = load_assertion_profile(PROFILE_PATH)
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    artifacts, documents = _fixtures()
    assertions = AssertionCompiler().compile(profile, artifacts, documents)
    assessment = TrustPolicy().assess(assertions)
    artifact_names = {artifact.id: artifact.filename for artifact in artifacts}

    actual_rows = sorted(
        (
            assertion.subject_id,
            assertion.predicate,
            json.dumps(assertion.value, sort_keys=True),
            artifact_names[assertion.evidence[0].artifact_id],
            assertion.status.value,
        )
        for assertion in assessment.assertions
    )
    expected_rows = sorted(
        (
            item["subject_id"],
            item["predicate"],
            json.dumps(item["value"], sort_keys=True),
            item["source"],
            item["expected_status"],
        )
        for item in expected["assertions"]
    )

    assert actual_rows == expected_rows
    assert len(assessment.conflicts) == expected["expected_conflicts"]


def test_runtime_profile_contains_patterns_not_predeclared_values() -> None:
    payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    assert all("value" not in rule for rule in payload["assertions"])
    assert all("quote" not in rule for rule in payload["assertions"])
    assert all("(?P<value>" in rule["evidence_pattern"] for rule in payload["assertions"])


def test_compiler_value_changes_when_extracted_evidence_changes() -> None:
    profile = load_assertion_profile(PROFILE_PATH)
    timeout_rule = next(
        rule for rule in profile.assertions if rule.predicate == "validation.timeout_seconds"
    )
    profile = profile.model_copy(update={"assertions": (timeout_rule,)})
    source = next(source for source in profile.sources if source.filename == timeout_rule.source)
    artifact = SourceArtifact(
        filename=source.filename,
        media_type="application/pdf",
        source_kind=source.source_kind,
        sha256="1" * 64,
        extraction_provider="test",
    )
    document = ExtractedDocument(
        provider="test",
        raw_response={"test": True},
        blocks=(
            ExtractedBlock(
                block_id="p1-b1",
                page=1,
                text="Synchronous validation\ntimeout is 45 seconds.",
            ),
        ),
    )

    assertions = AssertionCompiler().compile(profile, (artifact,), {source.filename: document})

    assert assertions[0].value == 45
    assert assertions[0].evidence[0].quote.endswith("45 seconds.")


def test_path_evidence_does_not_ignore_a_missing_slash() -> None:
    document = ExtractedDocument(
        provider="test",
        raw_response={"test": True},
        blocks=(
            ExtractedBlock(
                block_id="ocr-page-1",
                page=1,
                text="Canonical operation: POST V2/changes.",
            ),
        ),
    )

    assert (
        AssertionCompiler._find_evidence(
            "Canonical operation: [A-Z]+ (?P<value>/[A-Za-z0-9/{}_-]+)[.]",
            1,
            document,
        )
        is None
    )
