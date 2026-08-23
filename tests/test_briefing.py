import httpx
import pytest

from heatops.api import build_placement_plan
from heatops.briefing.evidence import create_evidence, evidence_fingerprint
from heatops.briefing.service import BriefingService, GroqBriefNarrator, TemplateBriefNarrator
from heatops.optimization.models import PlacementRequest
from heatops.providers.mock import MockTemperatureProvider


def request() -> PlacementRequest:
    return PlacementRequest.model_validate({
        "risk_map": {
            "heatmap": {
                "bounds": {
                    "north": 28.755,
                    "south": 28.705,
                    "east": -81.315,
                    "west": -81.375,
                },
                "metric": "snapshot",
                "threshold_c": 35,
            }
        },
        "resource_count": 3,
        "coverage_radius_km": 0.75,
    })


@pytest.mark.asyncio
async def test_template_brief_is_grounded_and_reproducible() -> None:
    plan = await build_placement_plan(request(), MockTemperatureProvider())
    service = BriefingService(template=TemplateBriefNarrator())

    first = await service.create_brief(plan)
    second = await service.create_brief(plan)

    assert first == second
    assert first.source == "template"
    assert first.grounded is True
    assert "3 cooling points" in first.headline
    assert first.evidence_fingerprint == evidence_fingerprint(create_evidence(plan))


@pytest.mark.asyncio
async def test_groq_narrator_uses_json_mode_and_validates_response() -> None:
    narrative = {
        "headline": "Deploy three sites",
        "situation_summary": "The optimized plan improves modeled coverage.",
        "deployment_actions": ["Deploy priority one first."],
        "watch_items": ["Re-run if capacity changes."],
        "limitations": ["This is decision support."],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-groq-key"
        assert b'"response_format":{"type":"json_object"}' in request.content
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": __import__("json").dumps(narrative)}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        narrator = GroqBriefNarrator(
            api_key="test-groq-key",
            model="qwen/qwen3.6-27b",
            client=client,
        )
        result = await narrator.narrate({"verified": True})

    assert result.headline == "Deploy three sites"
