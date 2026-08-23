import pytest

from heatops.domain import GeoBounds, HeatmapRequest
from heatops.optimization.candidates import CellCentroidCandidateProvider
from heatops.providers.mock import MockTemperatureProvider
from heatops.risk.context import SyntheticRiskContextProvider
from heatops.risk.engine import RiskEngine
from heatops.risk.models import RiskWeights


@pytest.mark.asyncio
async def test_candidate_provider_creates_one_centroid_per_cell() -> None:
    request = HeatmapRequest(
        bounds=GeoBounds(north=29, south=28, east=-81, west=-82),
    )
    heatmap = await MockTemperatureProvider(grid_size=2).create_heatmap(request)
    contexts = SyntheticRiskContextProvider().create_context(heatmap)
    risk_map = RiskEngine().assess(heatmap, contexts, RiskWeights(), request.threshold_c)

    candidates = CellCentroidCandidateProvider().create_candidates(risk_map)

    assert len(candidates) == 4
    assert {candidate.source_cell_id for candidate in candidates} == {
        feature.properties.cell_id for feature in risk_map.features
    }
    assert all(-82 < candidate.longitude < -81 for candidate in candidates)
    assert all(28 < candidate.latitude < 29 for candidate in candidates)
    assert all(candidate.source == "cell_centroid" for candidate in candidates)


@pytest.mark.asyncio
async def test_candidate_generation_is_deterministic() -> None:
    request = HeatmapRequest(
        bounds=GeoBounds(north=29, south=28, east=-81, west=-82),
    )
    heatmap = await MockTemperatureProvider(grid_size=3).create_heatmap(request)
    contexts = SyntheticRiskContextProvider().create_context(heatmap)
    risk_map = RiskEngine().assess(heatmap, contexts, RiskWeights(), request.threshold_c)
    provider = CellCentroidCandidateProvider()

    assert provider.create_candidates(risk_map) == provider.create_candidates(risk_map)

