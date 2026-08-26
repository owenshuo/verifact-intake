from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ExtractedBlock(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    block_id: str
    page: int = Field(ge=1)
    text: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    bounding_box: tuple[float, float, float, float] | None = None


class ExtractedDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    blocks: tuple[ExtractedBlock, ...]
    raw_response: dict[str, Any]


class DocumentExtractor(Protocol):
    async def extract(self, path: Path) -> ExtractedDocument: ...

