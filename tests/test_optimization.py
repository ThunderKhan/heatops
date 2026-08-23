import pytest

from heatops.domain import GeoBounds, HeatmapRequest
from heatops.optimization.candidates import CellCentroidCandidateProvider
from heatops.optimization.engine import PlacementOptimizer
from heatops.providers.mock import MockTemperatureProvider
from heatops.risk.context import SyntheticRiskContextProvider
from heatops.risk.engine import RiskEngine
from heatops.risk.models import RiskWeights


async def build_inputs(grid_size: int = 8):
    request = HeatmapRequest(
        bounds=GeoBounds(north=28.755, south=28.705, east=-81.315, west=-81.375),
    )
    heatmap = await MockTemperatureProvider(grid_size=grid_size).create_heatmap(request)
    contexts = SyntheticRiskContextProvider().create_context(heatmap)
    risk_map = RiskEngine().assess(heatmap, contexts, RiskWeights(), request.threshold_c)
    candidates = CellCentroidCandidateProvider().create_candidates(risk_map)
    return risk_map, candidates


def test_haversine_distance_is_symmetric_and_zero_on_identity() -> None:
    optimizer = PlacementOptimizer()

    assert optimizer.haversine_km(77, 28, 77, 28) == 0
    forward = optimizer.haversine_km(77, 28, 77.1, 28.1)
    reverse = optimizer.haversine_km(77.1, 28.1, 77, 28)
    assert forward == pytest.approx(reverse)


@pytest.mark.asyncio
async def test_optimizer_is_deterministic_and_never_worse_than_baseline() -> None:
    risk_map, candidates = await build_inputs()
    optimizer = PlacementOptimizer()

    first = optimizer.optimize(risk_map, candidates, 5, 0.75)
    second = optimizer.optimize(risk_map, candidates, 5, 0.75)

    assert first == second
    assert first.optimized.covered_risk_burden >= first.baseline.covered_risk_burden
    assert first.improvement_percentage_points >= 0
    assert first.optimized.selected_resource_count <= 5


@pytest.mark.asyncio
async def test_more_resources_do_not_reduce_optimized_coverage() -> None:
    risk_map, candidates = await build_inputs()
    optimizer = PlacementOptimizer()

    three = optimizer.optimize(risk_map, candidates, 3, 0.75)
    five = optimizer.optimize(risk_map, candidates, 5, 0.75)

    assert five.optimized.covered_risk_burden >= three.optimized.covered_risk_burden
    assert set(three.optimized.covered_cell_ids) <= set(five.optimized.covered_cell_ids)


@pytest.mark.asyncio
async def test_plan_accounting_matches_selected_marginal_gains() -> None:
    risk_map, candidates = await build_inputs()
    result = PlacementOptimizer().optimize(risk_map, candidates, 4, 0.75)

    marginal_total = sum(
        placement.marginal_covered_risk for placement in result.optimized.placements
    )
    assert marginal_total == pytest.approx(result.optimized.covered_risk_burden, abs=5e-6)
    assert result.optimized.covered_cell_count == len(result.optimized.covered_cell_ids)
    assert len({placement.site.site_id for placement in result.optimized.placements}) == (
        result.optimized.selected_resource_count
    )


@pytest.mark.asyncio
async def test_larger_radius_does_not_reduce_coverage() -> None:
    risk_map, candidates = await build_inputs()
    optimizer = PlacementOptimizer()

    narrow = optimizer.optimize(risk_map, candidates, 4, 0.4)
    wide = optimizer.optimize(risk_map, candidates, 4, 1.0)

    assert wide.optimized.covered_risk_burden >= narrow.optimized.covered_risk_burden


@pytest.mark.asyncio
async def test_optimizer_rejects_empty_candidates() -> None:
    risk_map, _ = await build_inputs(grid_size=2)

    with pytest.raises(ValueError, match="at least one candidate"):
        PlacementOptimizer().optimize(risk_map, (), 2, 0.75)

