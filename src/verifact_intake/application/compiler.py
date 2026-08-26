from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from verifact_intake.domain.models import Assertion, EvidenceLocator, FrozenModel, SourceArtifact
from verifact_intake.ports.document_extractor import ExtractedBlock, ExtractedDocument


class AssertionRule(FrozenModel):
    subject_id: str
    predicate: str
    value: Any
    source: str
    page: int = Field(ge=1)
    quote: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    authority: int = Field(ge=0, le=100)
    expected_status: str


class GoldenDataset(FrozenModel):
    dataset: str
    description: str
    assertions: tuple[AssertionRule, ...]
    expected_conflicts: int = Field(ge=0)
    expected_effective_facts_after_review: dict[str, Any]


class EvidenceCompilationError(RuntimeError):
    """Raised when a declared assertion cannot be tied to extracted evidence."""


def load_golden_dataset(path: Path) -> GoldenDataset:
    payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    return GoldenDataset.model_validate(payload)


class AssertionCompiler:
    """Compile declared semantic rules only when extraction provides matching evidence."""

    def compile(
        self,
        dataset: GoldenDataset,
        artifacts: tuple[SourceArtifact, ...],
        documents: dict[str, ExtractedDocument],
    ) -> tuple[Assertion, ...]:
        artifact_by_name = {artifact.filename: artifact for artifact in artifacts}
        compiled: list[Assertion] = []
        missing: list[str] = []

        for rule in dataset.assertions:
            artifact = artifact_by_name.get(rule.source)
            document = documents.get(rule.source)
            if artifact is None or document is None:
                missing.append(f"{rule.source}: source was not extracted")
                continue
            block = self._find_evidence(rule.quote, rule.page, document)
            if block is None:
                missing.append(f"{rule.source}: {rule.quote}")
                continue
            confidence = min(
                rule.confidence,
                block.confidence if block.confidence is not None else rule.confidence,
            )
            compiled.append(
                Assertion(
                    subject_id=rule.subject_id,
                    predicate=rule.predicate,
                    value=rule.value,
                    confidence=confidence,
                    authority=rule.authority,
                    evidence=(
                        EvidenceLocator(
                            artifact_id=artifact.id,
                            page=block.page,
                            quote=rule.quote,
                            block_id=block.block_id,
                            bounding_box=block.bounding_box,
                        ),
                    ),
                )
            )

        if missing:
            details = "; ".join(missing)
            raise EvidenceCompilationError(f"Evidence compilation failed: {details}")
        return tuple(compiled)

    @classmethod
    def _find_evidence(
        cls, quote: str, page: int, document: ExtractedDocument
    ) -> ExtractedBlock | None:
        normalized_quote = cls._normalize(quote)
        same_page = [block for block in document.blocks if block.page == page]
        for block in same_page:
            if normalized_quote in cls._normalize(block.text):
                return block
        for block in document.blocks:
            if normalized_quote in cls._normalize(block.text):
                return block
        return None

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
