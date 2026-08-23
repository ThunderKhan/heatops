import pytest
from pydantic import ValidationError

from heatops.domain import GeoBounds, HeatmapRequest, HeatMetric
from heatops.providers.mock import MockTemperatureProvider
from heatops.risk.context import SyntheticRiskContextProvider
from heatops.risk.engine import RiskEngine
from heatops.risk.models import RiskContext, RiskLevel, RiskWeights


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValidationError, match="sum to 1.0"):
        RiskWeights(exposure=0.5, vulnerability=0.5, lack_of_access=0.5)


@pytest.mark.parametrize(
    ("metric", "value", "threshold", "expected"),
    [
        (HeatMetric.SNAPSHOT, 30.0, 35.0, 0.0),
        (HeatMetric.SNAPSHOT, 35.0, 35.0, 0.5),
        (HeatMetric.SNAPSHOT, 40.0, 35.0, 1.0),
        (HeatMetric.EXCEEDANCE, 6.0, 35.0, 0.5),
        (HeatMetric.PERSISTENCE, 4.0, 35.0, 0.5),
    ],
)
def test_hazard_normalization(
    metric: HeatMetric,
    value: float,
    threshold: float,
    expected: float,
) -> None:
    assert RiskEngine.normalize_hazard(metric, value, threshold) == expected


def test_zero_hazard_produces_zero_risk() -> None:
    context = RiskContext(
        cell_id="cell",
        exposure=1,
        vulnerability=1,
        cooling_access=0,
        source="synthetic",
    )

    result = RiskEngine.calculate_score(0, context, RiskWeights())

    assert result.score == 0
    assert result.level is RiskLevel.LOW


def test_more_cooling_access_reduces_risk() -> None:
    low_access = RiskContext(
        cell_id="cell",
        exposure=0.8,
        vulnerability=0.8,
        cooling_access=0.1,
        source="synthetic",
    )
    high_access = low_access.model_copy(update={"cooling_access": 0.9})

    low_access_score = RiskEngine.calculate_score(0.9, low_access, RiskWeights()).score
    high_access_score = RiskEngine.calculate_score(0.9, high_access, RiskWeights()).score

    assert high_access_score < low_access_score


def test_contributions_reconstruct_score() -> None:
    context = RiskContext(
        cell_id="cell",
        exposure=0.65,
        vulnerability=0.8,
        cooling_access=0.2,
        source="synthetic",
    )

    result = RiskEngine.calculate_score(0.75, context, RiskWeights())

    reconstructed = (
        result.exposure_contribution
        + result.vulnerability_contribution
        + result.access_contribution
    )
    assert reconstructed == pytest.approx(result.score, abs=2e-6)


@pytest.mark.asyncio
async def test_assessment_preserves_geometry_and_builds_summary() -> None:
    request = HeatmapRequest(
        bounds=GeoBounds(north=29, south=28, east=-81, west=-82),
        metric=HeatMetric.SNAPSHOT,
        threshold_c=35,
    )
    heatmap = await MockTemperatureProvider(grid_size=3).create_heatmap(request)
    contexts = SyntheticRiskContextProvider().create_context(heatmap)

    result = RiskEngine().assess(heatmap, contexts, RiskWeights(), request.threshold_c)

    assert len(result.features) == 9
    assert result.summary.cell_count == 9
    assert sum(result.summary.level_counts.values()) == 9
    assert result.synthetic is True
    assert result.features[0].geometry == heatmap.features[0].geometry
    assert all(0 <= feature.properties.risk_score <= 1 for feature in result.features)


@pytest.mark.asyncio
async def test_assessment_rejects_missing_context() -> None:
    request = HeatmapRequest(
        bounds=GeoBounds(north=29, south=28, east=-81, west=-82),
    )
    heatmap = await MockTemperatureProvider(grid_size=2).create_heatmap(request)

    with pytest.raises(ValueError, match="missing risk context"):
        RiskEngine().assess(heatmap, (), RiskWeights(), request.threshold_c)

