import pytest

from heatops.domain import GeoBounds, HeatmapRequest
from heatops.providers.mock import MockTemperatureProvider
from heatops.risk.context import SyntheticRiskContextProvider


@pytest.mark.asyncio
async def test_synthetic_context_is_complete_bounded_and_deterministic() -> None:
    heatmap = await MockTemperatureProvider(grid_size=3).create_heatmap(
        HeatmapRequest(
            bounds=GeoBounds(north=29, south=28, east=-81, west=-82),
        )
    )
    provider = SyntheticRiskContextProvider()

    first = provider.create_context(heatmap)
    second = provider.create_context(heatmap)

    assert first == second
    assert len(first) == len(heatmap.features)
    assert {context.cell_id for context in first} == {
        feature.properties.cell_id for feature in heatmap.features
    }
    for context in first:
        assert 0 <= context.exposure <= 1
        assert 0 <= context.vulnerability <= 1
        assert 0 <= context.cooling_access <= 1
        assert context.source == "synthetic"


def test_context_fallback_supports_non_mock_identifiers() -> None:
    first = SyntheticRiskContextProvider._context_for("external-cell-42")
    second = SyntheticRiskContextProvider._context_for("external-cell-42")

    assert first == second
    assert first.cell_id == "external-cell-42"

