import httpx
import pytest

from heatops.domain import GeoBounds, HeatmapRequest, HeatMetric
from heatops.providers.fortyguard import FortyGuardError, FortyGuardTemperatureProvider


def feature_collection(value: float = 37.5) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-81.375, 28.705],
                    [-81.365, 28.705],
                    [-81.365, 28.715],
                    [-81.375, 28.715],
                    [-81.375, 28.705],
                ]],
            },
            "properties": {"temperature": value},
        }],
    }


@pytest.mark.asyncio
async def test_fortyguard_provider_submits_polls_and_converts_geojson() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(
                200,
                json={"data": {"activity_id": "activity-123"}},
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "status": "Completed",
                    "result": {"map_data": feature_collection()},
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = FortyGuardTemperatureProvider(
            api_key="test-key",
            client=client,
            poll_interval_seconds=0,
        )
        result = await provider.create_heatmap(
            HeatmapRequest(
                bounds=GeoBounds(north=28.755, south=28.705, east=-81.315, west=-81.375),
                metric=HeatMetric.SNAPSHOT,
                start_date="2026-08-23",
                start_time_utc="14:00",
            )
        )

    assert [request.url.path for request in requests] == [
        "/v1/heatmap",
        "/v1/status/activity-123",
    ]
    submitted = __import__("json").loads(requests[0].content)
    assert submitted["analytic_type"] == "tcm"
    assert submitted["date_time"] == {
        "start_date": "2026-08-23",
        "start_time": "14:00",
        "filter_type": 1,
    }
    assert result.synthetic is False
    assert result.features[0].properties.value == 37.5
    assert result.features[0].properties.source == "fortyguard"


@pytest.mark.asyncio
async def test_fortyguard_provider_surfaces_failed_activity() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={"data": {"activity_id": "failed-123"}})
        return httpx.Response(200, json={"message": "quota", "data": {"status": "Failed"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = FortyGuardTemperatureProvider(api_key="test-key", client=client)
        with pytest.raises(FortyGuardError, match="quota"):
            await provider.create_heatmap(
                HeatmapRequest(
                    bounds=GeoBounds(
                        north=28.755,
                        south=28.705,
                        east=-81.315,
                        west=-81.375,
                    )
                )
            )
