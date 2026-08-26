from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

import httpx

from verifact_intake.ports.document_extractor import ExtractedBlock, ExtractedDocument


class NutrientExtractionError(RuntimeError):
    """Raised when Nutrient DWS cannot return a usable extraction result."""


class NutrientDocumentExtractor:
    """Nutrient DWS adapter for the challenge's core extraction operation."""

    CACHE_SCHEMA = "verifact.nutrient-cache/v1"
    INSTRUCTIONS_VERSION = "json-content-key-value-pairs/v1"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.nutrient.io",
        live_mode: bool = False,
        cache_dir: Path | None = None,
        cache_enabled: bool = True,
        cache_refresh: bool = False,
        max_live_calls: int = 3,
        estimated_credits_per_call: float = 3.0,
        max_estimated_credits: float = 9.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if live_mode and (api_key is None or not api_key.strip()):
            raise ValueError("A non-empty Nutrient API key is required in live mode")
        if max_live_calls < 1:
            raise ValueError("max_live_calls must be at least 1")
        if estimated_credits_per_call <= 0 or max_estimated_credits <= 0:
            raise ValueError("Estimated credit limits must be positive")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._live_mode = live_mode
        self._cache_dir = cache_dir
        self._cache_enabled = cache_enabled
        self._cache_refresh = cache_refresh
        self._max_live_calls = max_live_calls
        self._estimated_credits_per_call = estimated_credits_per_call
        self._max_estimated_credits = max_estimated_credits
        self._live_calls = 0
        self._estimated_credits_used = 0.0
        self._request_lock = asyncio.Lock()
        self._client = client

    async def extract(self, path: Path) -> ExtractedDocument:
        # Serializing cache lookup and submission prevents concurrent identical
        # runs from both observing a miss and spending credits twice.
        async with self._request_lock:
            return await self._extract_serialized(path)

    async def _extract_serialized(self, path: Path) -> ExtractedDocument:
        instructions = self._instructions()
        cache_key, input_sha256, instructions_sha256 = self._cache_identity(path, instructions)
        if self._cache_enabled and not self._cache_refresh:
            cached = self._load_cache(
                cache_key,
                input_sha256=input_sha256,
                instructions_sha256=instructions_sha256,
            )
            if cached is not None:
                return self._document_from_payload(cached, provider="nutrient-dws-cache")

        if not self._live_mode:
            raise NutrientExtractionError(
                f"No cached Nutrient response exists for {path.name}; "
                "set NUTRIENT_LIVE_MODE=true to permit a billable request"
            )
        self._reserve_live_budget(path)
        assert self._api_key is not None
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
        except (OSError, httpx.RequestError) as exc:
            raise NutrientExtractionError(f"Nutrient extraction failed for {path.name}") from exc

        if response.status_code == 402:
            raise NutrientExtractionError(
                "Nutrient rejected the request because credits are insufficient; "
                "the adapter did not retry"
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise NutrientExtractionError(
                f"Nutrient extraction failed for {path.name} with HTTP {response.status_code}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise NutrientExtractionError("Nutrient returned a non-JSON response") from exc
        if not isinstance(payload, dict):
            raise NutrientExtractionError("Nutrient returned an unexpected JSON response")

        # Persist the raw successful response before mapping it. If Nutrient adds
        # a new payload shape, the adapter can be repaired against the cache
        # instead of spending another credit to reproduce the response.
        if self._cache_enabled:
            self._save_cache(
                cache_key,
                payload=payload,
                input_sha256=input_sha256,
                instructions_sha256=instructions_sha256,
            )
        return self._document_from_payload(payload, provider="nutrient-dws-live")

    def _document_from_payload(
        self, payload: dict[str, Any], *, provider: str
    ) -> ExtractedDocument:
        blocks = tuple(self._map_blocks(payload))
        if not blocks:
            raise NutrientExtractionError("Nutrient returned no extractable blocks")
        return ExtractedDocument(provider=provider, blocks=blocks, raw_response=payload)

    def _reserve_live_budget(self, path: Path) -> None:
        if self._live_calls >= self._max_live_calls:
            raise NutrientExtractionError(
                f"Live-call budget exhausted before {path.name}; no request was sent"
            )
        projected = self._estimated_credits_used + self._estimated_credits_per_call
        if projected > self._max_estimated_credits:
            raise NutrientExtractionError(
                f"Estimated credit budget would be exceeded before {path.name}; no request was sent"
            )
        self._live_calls += 1
        self._estimated_credits_used = projected

    @classmethod
    def _instructions(cls) -> dict[str, Any]:
        return {
            "parts": [{"file": "document"}],
            "output": {"type": "json-content", "keyValuePairs": True},
        }

    @classmethod
    def _cache_identity(
        cls, path: Path, instructions: dict[str, Any]
    ) -> tuple[str, str, str]:
        try:
            input_bytes = path.read_bytes()
        except OSError as exc:
            raise NutrientExtractionError(f"Unable to read {path.name}") from exc
        input_sha256 = hashlib.sha256(input_bytes).hexdigest()
        instruction_material = json.dumps(
            {"version": cls.INSTRUCTIONS_VERSION, "instructions": instructions},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        instructions_sha256 = hashlib.sha256(instruction_material).hexdigest()
        cache_key = hashlib.sha256(
            f"{input_sha256}:{instructions_sha256}".encode()
        ).hexdigest()
        return cache_key, input_sha256, instructions_sha256

    def _cache_path(self, cache_key: str) -> Path | None:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{cache_key}.json"

    def _load_cache(
        self,
        cache_key: str,
        *,
        input_sha256: str,
        instructions_sha256: str,
    ) -> dict[str, Any] | None:
        cache_path = self._cache_path(cache_key)
        if cache_path is None or not cache_path.is_file():
            return None
        try:
            envelope = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise NutrientExtractionError(
                f"Cached Nutrient response is unreadable: {cache_path.name}"
            ) from exc
        if not isinstance(envelope, dict):
            raise NutrientExtractionError("Cached Nutrient response has an invalid envelope")
        if (
            envelope.get("schema") != self.CACHE_SCHEMA
            or envelope.get("input_sha256") != input_sha256
            or envelope.get("instructions_sha256") != instructions_sha256
        ):
            raise NutrientExtractionError("Cached Nutrient response failed identity validation")
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise NutrientExtractionError("Cached Nutrient response has no valid payload")
        return payload

    def _save_cache(
        self,
        cache_key: str,
        *,
        payload: dict[str, Any],
        input_sha256: str,
        instructions_sha256: str,
    ) -> None:
        cache_path = self._cache_path(cache_key)
        if cache_path is None:
            return
        envelope = {
            "schema": self.CACHE_SCHEMA,
            "input_sha256": input_sha256,
            "instructions_sha256": instructions_sha256,
            "payload": payload,
        }
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(envelope, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            temporary.replace(cache_path)
        except OSError as exc:
            raise NutrientExtractionError(
                f"Unable to persist Nutrient cache entry for {cache_path.name}"
            ) from exc

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
