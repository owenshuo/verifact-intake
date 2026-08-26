from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, cast

from pydantic import Field, field_validator, model_validator

from verifact_intake.domain.models import (
    Assertion,
    EvidenceLocator,
    FrozenModel,
    SourceArtifact,
    SourceKind,
)
from verifact_intake.ports.document_extractor import ExtractedBlock, ExtractedDocument


class ValueType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class SourceDefinition(FrozenModel):
    filename: str = Field(min_length=1, max_length=255)
    source_kind: SourceKind


class AssertionRule(FrozenModel):
    subject_id: str
    predicate: str
    source: str
    page: int = Field(ge=1)
    evidence_pattern: str = Field(min_length=1)
    value_type: ValueType
    confidence: float = Field(ge=0, le=1)
    authority: int = Field(ge=0, le=100)

    @field_validator("evidence_pattern")
    @classmethod
    def pattern_must_capture_value(cls, value: str) -> str:
        try:
            pattern = re.compile(value, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"invalid evidence pattern: {exc}") from exc
        if "value" not in pattern.groupindex:
            raise ValueError("evidence_pattern must contain a named 'value' group")
        return value


class AssertionProfile(FrozenModel):
    schema_name: str = Field(alias="schema", pattern=r"^verifact\.assertion-profile/v\d+$")
    profile: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    description: str = Field(min_length=1)
    sources: tuple[SourceDefinition, ...] = Field(min_length=1)
    assertions: tuple[AssertionRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def rules_must_reference_declared_sources(self) -> AssertionProfile:
        filenames = [source.filename for source in self.sources]
        if len(filenames) != len(set(filenames)):
            raise ValueError("profile source filenames must be unique")
        undeclared = sorted(
            {rule.source for rule in self.assertions if rule.source not in filenames}
        )
        if undeclared:
            raise ValueError(f"assertion rules reference undeclared sources: {undeclared}")
        return self


class EvidenceCompilationError(RuntimeError):
    """Raised when extracted document content cannot satisfy a declared rule."""


@dataclass(frozen=True)
class EvidenceMatch:
    block: ExtractedBlock
    quote: str
    raw_value: str


def load_assertion_profile(path: Path) -> AssertionProfile:
    payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    return AssertionProfile.model_validate(payload)


class AssertionCompiler:
    """Derive typed assertion values from DWS-extracted evidence blocks."""

    _INTEGER_WORDS: ClassVar[dict[str, int]] = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    _TRUE_VALUES: ClassVar[set[str]] = {"required", "mandatory", "true", "yes"}
    _FALSE_VALUES: ClassVar[set[str]] = {
        "optional",
        "not required",
        "false",
        "no",
    }

    def compile(
        self,
        profile: AssertionProfile,
        artifacts: tuple[SourceArtifact, ...],
        documents: dict[str, ExtractedDocument],
    ) -> tuple[Assertion, ...]:
        artifact_by_name = {artifact.filename: artifact for artifact in artifacts}
        compiled: list[Assertion] = []
        missing: list[str] = []

        for rule in profile.assertions:
            artifact = artifact_by_name.get(rule.source)
            document = documents.get(rule.source)
            if artifact is None or document is None:
                missing.append(f"{rule.source}: source was not extracted")
                continue
            evidence = self._find_evidence(rule.evidence_pattern, rule.page, document)
            if evidence is None:
                missing.append(f"{rule.source}: pattern {rule.evidence_pattern!r}")
                continue
            try:
                value = self._coerce_value(evidence.raw_value, rule.value_type)
            except ValueError as exc:
                missing.append(f"{rule.source}: {exc}")
                continue
            confidence = min(
                rule.confidence,
                evidence.block.confidence
                if evidence.block.confidence is not None
                else rule.confidence,
            )
            compiled.append(
                Assertion(
                    subject_id=rule.subject_id,
                    predicate=rule.predicate,
                    value=value,
                    confidence=confidence,
                    authority=rule.authority,
                    evidence=(
                        EvidenceLocator(
                            artifact_id=artifact.id,
                            page=evidence.block.page,
                            quote=evidence.quote,
                            block_id=evidence.block.block_id,
                            bounding_box=evidence.block.bounding_box,
                        ),
                    ),
                )
            )

        if missing:
            details = "; ".join(missing)
            raise EvidenceCompilationError(f"Evidence compilation failed: {details}")
        return tuple(compiled)

    @staticmethod
    def _find_evidence(
        evidence_pattern: str, page: int, document: ExtractedDocument
    ) -> EvidenceMatch | None:
        pattern = re.compile(evidence_pattern, re.IGNORECASE)
        preferred = [block for block in document.blocks if block.page == page]
        fallback = [block for block in document.blocks if block.page != page]
        for block in (*preferred, *fallback):
            normalized_text = re.sub(r"\s+", " ", block.text).strip()
            match = pattern.search(normalized_text)
            if match is not None:
                return EvidenceMatch(
                    block=block,
                    quote=match.group(0).strip(),
                    raw_value=match.group("value").strip(),
                )
        return None

    @classmethod
    def _coerce_value(cls, raw_value: str, value_type: ValueType) -> object:
        normalized = re.sub(r"\s+", " ", raw_value).strip()
        if value_type is ValueType.STRING:
            return normalized
        if value_type is ValueType.INTEGER:
            lowered = normalized.lower()
            if lowered in cls._INTEGER_WORDS:
                return cls._INTEGER_WORDS[lowered]
            try:
                return int(normalized)
            except ValueError as exc:
                raise ValueError(f"cannot coerce {raw_value!r} to integer") from exc
        lowered = normalized.lower()
        if lowered in cls._TRUE_VALUES:
            return True
        if lowered in cls._FALSE_VALUES:
            return False
        raise ValueError(f"cannot coerce {raw_value!r} to boolean")
