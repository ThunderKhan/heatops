import pytest

from heatops.domain import GeoBounds, HeatmapRequest, HeatMetric
from heatops.providers.mock import MockTemperatureProvider

BOUNDS = GeoBounds(north=28.755, south=28.705, east=-81.315, west=-81.375)


@pytest.mark.parametrize(
    ("metric", "expected_unit"),
    [
        (HeatMetric.SNAPSHOT, "celsius"),
        (HeatMetric.EXCEEDANCE, "hours"),
        (HeatMetric.PERSISTENCE, "hours"),
    ],
)
@pytest.mark.asyncio
async def test_provider_preserves_metric_units(
    metric: HeatMetric,
    expected_unit: str,
) -> None:
    provider = MockTemperatureProvider(grid_size=4)

    result = await provider.create_heatmap(
        HeatmapRequest(bounds=BOUNDS, metric=metric, threshold_c=35.0)
    )

    assert result.synthetic is True
    assert len(result.features) == 16
    assert {feature.properties.unit for feature in result.features} == {expected_unit}
    assert {feature.properties.source for feature in result.features} == {"synthetic"}


@pytest.mark.asyncio
async def test_provider_is_deterministic() -> None:
    provider = MockTemperatureProvider(grid_size=3)
    request = HeatmapRequest(bounds=BOUNDS)

    first = await provider.create_heatmap(request)
    second = await provider.create_heatmap(request)

    assert first == second


@pytest.mark.asyncio
async def test_persistence_never_exceeds_total_exceedance() -> None:
    provider = MockTemperatureProvider(grid_size=5)
    exceedance = await provider.create_heatmap(
        HeatmapRequest(bounds=BOUNDS, metric=HeatMetric.EXCEEDANCE, threshold_c=34.0)
    )
    persistence = await provider.create_heatmap(
        HeatmapRequest(bounds=BOUNDS, metric=HeatMetric.PERSISTENCE, threshold_c=34.0)
    )

    exceedance_by_cell = {
        feature.properties.cell_id: feature.properties.value for feature in exceedance.features
    }
    for feature in persistence.features:
        assert feature.properties.value <= exceedance_by_cell[feature.properties.cell_id]

