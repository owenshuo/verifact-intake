import asyncio
from pathlib import Path

import httpx
import pytest

from verifact_intake.adapters.nutrient import (
    NutrientDocumentExtractor,
    NutrientExtractionError,
)


@pytest.mark.asyncio
async def test_nutrient_adapter_posts_document_and_maps_blocks(tmp_path: Path) -> None:
    document = tmp_path / "guide.pdf"
    document.write_bytes(b"%PDF-1.4 synthetic")
    request_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
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
            live_mode=True,
            cache_dir=tmp_path / "cache",
            client=client,
        )
        result = await extractor.extract(document)
        cached = await extractor.extract(document)

    assert request_count == 1
    assert result.provider == "nutrient-dws-live"
    assert cached.provider == "nutrient-dws-cache"
    assert cached.raw_response == result.raw_response
    assert result.blocks[0].page == 1
    assert result.blocks[0].text.startswith("POST")


@pytest.mark.asyncio
async def test_nutrient_adapter_requires_explicit_live_mode_on_cache_miss(
    tmp_path: Path,
) -> None:
    document = tmp_path / "guide.pdf"
    document.write_bytes(b"%PDF-1.4 synthetic")
    request_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = NutrientDocumentExtractor(
            cache_dir=tmp_path / "cache",
            client=client,
        )
        with pytest.raises(NutrientExtractionError, match="NUTRIENT_LIVE_MODE=true"):
            await extractor.extract(document)

    assert request_count == 0


@pytest.mark.asyncio
async def test_nutrient_adapter_does_not_retry_payment_required(tmp_path: Path) -> None:
    document = tmp_path / "guide.pdf"
    document.write_bytes(b"%PDF-1.4 synthetic")
    request_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(402, json={"error": "payment required"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = NutrientDocumentExtractor(
            api_key="test-key",
            base_url="https://api.nutrient.test",
            live_mode=True,
            cache_dir=tmp_path / "cache",
            client=client,
        )
        with pytest.raises(NutrientExtractionError, match="did not retry"):
            await extractor.extract(document)

    assert request_count == 1


@pytest.mark.asyncio
async def test_nutrient_adapter_stops_before_exceeding_live_budget(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    first.write_bytes(b"%PDF-1.4 first")
    second.write_bytes(b"%PDF-1.4 second")
    request_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json={"pages": [{"plainText": "Evidence."}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = NutrientDocumentExtractor(
            api_key="test-key",
            base_url="https://api.nutrient.test",
            live_mode=True,
            cache_dir=tmp_path / "cache",
            max_live_calls=1,
            estimated_credits_per_call=3,
            max_estimated_credits=3,
            client=client,
        )
        await extractor.extract(first)
        with pytest.raises(NutrientExtractionError, match="budget exhausted"):
            await extractor.extract(second)

    assert request_count == 1


@pytest.mark.asyncio
async def test_nutrient_adapter_singleflights_concurrent_identical_inputs(
    tmp_path: Path,
) -> None:
    document = tmp_path / "guide.pdf"
    document.write_bytes(b"%PDF-1.4 synthetic")
    request_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        await asyncio.sleep(0.01)
        return httpx.Response(200, json={"pages": [{"plainText": "Evidence."}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = NutrientDocumentExtractor(
            api_key="test-key",
            base_url="https://api.nutrient.test",
            live_mode=True,
            cache_dir=tmp_path / "cache",
            client=client,
        )
        first, second = await asyncio.gather(
            extractor.extract(document),
            extractor.extract(document),
        )

    assert request_count == 1
    assert {first.provider, second.provider} == {
        "nutrient-dws-live",
        "nutrient-dws-cache",
    }


@pytest.mark.asyncio
async def test_nutrient_adapter_caches_successful_raw_payload_before_mapping(
    tmp_path: Path,
) -> None:
    document = tmp_path / "guide.pdf"
    document.write_bytes(b"%PDF-1.4 synthetic")
    request_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json={"pages": [{"keyValuePairs": []}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = NutrientDocumentExtractor(
            api_key="test-key",
            base_url="https://api.nutrient.test",
            live_mode=True,
            cache_dir=tmp_path / "cache",
            client=client,
        )
        with pytest.raises(NutrientExtractionError, match="no extractable blocks"):
            await extractor.extract(document)
        with pytest.raises(NutrientExtractionError, match="no extractable blocks"):
            await extractor.extract(document)

    assert request_count == 1


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
