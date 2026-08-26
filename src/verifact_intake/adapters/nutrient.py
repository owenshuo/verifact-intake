from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from verifact_intake.ports.document_extractor import ExtractedBlock, ExtractedDocument


class NutrientExtractionError(RuntimeError):
    """Raised when Nutrient DWS cannot return a usable extraction result."""


class NutrientDocumentExtractor:
    """Nutrient DWS adapter for the challenge's core extraction operation."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.nutrient.io",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("A non-empty Nutrient API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client

    async def extract(self, path: Path) -> ExtractedDocument:
        instructions = {
            "parts": [{"file": "document"}],
            "output": {"type": "json-content", "keyValuePairs": True},
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            with path.open("rb") as source:
                files = {"document": (path.name, source, "application/pdf")}
                data = {"instructions": json.dumps(instructions)}
                if self._client is not None:
                    response = await self._client.post(
                        f"{self._base_url}/build",
                        headers=headers,
                        files=files,
                        data=data,
                    )
                else:
                    async with httpx.AsyncClient(timeout=60) as client:
                        response = await client.post(
                            f"{self._base_url}/build",
                            headers=headers,
                            files=files,
                            data=data,
                        )
            response.raise_for_status()
        except (OSError, httpx.HTTPError) as exc:
            raise NutrientExtractionError(f"Nutrient extraction failed for {path.name}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise NutrientExtractionError("Nutrient returned a non-JSON response") from exc

        blocks = tuple(self._map_blocks(payload))
        if not blocks:
            raise NutrientExtractionError("Nutrient returned no extractable blocks")
        return ExtractedDocument(provider="nutrient-dws", blocks=blocks, raw_response=payload)

    @staticmethod
    def _map_blocks(payload: dict[str, Any]) -> list[ExtractedBlock]:
        """Normalize likely DWS JSON-content shapes without hiding the raw response."""

        candidates = payload.get("blocks") or payload.get("content") or payload.get("pages") or []
        blocks: list[ExtractedBlock] = []
        if not isinstance(candidates, list):
            return blocks
        for index, item in enumerate(candidates, start=1):
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("content") or item.get("plainText")
            if not isinstance(text, str) or not text.strip():
                continue
            page_value = item.get("page")
            if page_value is None:
                page_index = item.get("pageIndex")
                page_value = page_index + 1 if isinstance(page_index, int) else index
            confidence = item.get("confidence")
            blocks.append(
                ExtractedBlock(
                    block_id=str(item.get("id") or f"block-{index}"),
                    page=max(int(page_value), 1),
                    text=text.strip(),
                    confidence=float(confidence) if confidence is not None else None,
                )
            )
        return blocks
