from pathlib import Path

import httpx
import pytest

from verifact_intake.adapters.nutrient import NutrientDocumentExtractor


@pytest.mark.asyncio
async def test_nutrient_adapter_posts_document_and_maps_blocks(tmp_path: Path) -> None:
    document = tmp_path / "guide.pdf"
    document.write_bytes(b"%PDF-1.4 synthetic")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://api.nutrient.test/build")
        assert request.headers["Authorization"] == "Bearer test-key"
        assert b"json-content" in await request.aread()
        return httpx.Response(
            200,
            json={
                "blocks": [
                    {
                        "id": "p1-b1",
                        "page": 1,
                        "text": "POST /changes creates a change request.",
                        "confidence": 0.99,
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = NutrientDocumentExtractor(
            api_key="test-key",
            base_url="https://api.nutrient.test",
            client=client,
        )
        result = await extractor.extract(document)

    assert result.provider == "nutrient-dws"
    assert result.blocks[0].page == 1
    assert result.blocks[0].text.startswith("POST")


def test_nutrient_adapter_maps_live_json_content_page_shape() -> None:
    blocks = NutrientDocumentExtractor._map_blocks(
        {
            "pages": [
                {
                    "plainText": "The service base path is /change-api.",
                    "keyValuePairs": [{"key": "Version", "value": "2.1"}],
                },
                {"plainText": "Second page evidence."},
            ]
        }
    )

    assert [block.page for block in blocks] == [1, 2]
    assert blocks[0].text == "The service base path is /change-api."
