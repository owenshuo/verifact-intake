from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from verifact_intake.ports.document_extractor import ExtractedDocument


class FixtureDocumentExtractor:
    """Offline adapter using checked-in responses shaped like the DWS port."""

    def __init__(self, fixture_dir: Path) -> None:
        self._fixture_dir = fixture_dir

    async def extract(self, path: Path) -> ExtractedDocument:
        fixture_path = self._fixture_dir / f"{path.stem}.json"
        payload = cast(
            dict[str, Any], json.loads(fixture_path.read_text(encoding="utf-8"))
        )
        return ExtractedDocument.model_validate(payload)
