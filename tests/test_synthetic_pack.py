import json
import re
from pathlib import Path

import pdfplumber

from verifact_intake.application.compiler import AssertionCompiler
from verifact_intake.ports.document_extractor import ExtractedBlock, ExtractedDocument

ROOT = Path(__file__).resolve().parents[1]


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def test_every_golden_quote_exists_in_its_source_pdf() -> None:
    golden_path = ROOT / "data" / "synthetic" / "golden" / "assertions.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    source_text: dict[str, str] = {}

    for item in golden["assertions"]:
        filename = item["source"]
        if filename not in source_text:
            with pdfplumber.open(ROOT / "output" / "pdf" / filename) as document:
                source_text[filename] = normalize(
                    " ".join(page.extract_text() or "" for page in document.pages)
                )
        assert normalize(item["quote"]) in source_text[filename]


def test_fixture_blocks_are_public_safe_and_match_pdf_names() -> None:
    fixture_dir = ROOT / "data" / "synthetic" / "fixtures"
    for path in fixture_dir.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["provider"] == "fixture"
        assert payload["raw_response"]["document"] == f"{path.stem}.pdf"
        assert payload["blocks"]


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
            "Canonical operation: POST /v2/changes.", 1, document
        )
        is None
    )
