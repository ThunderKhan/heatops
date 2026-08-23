from functools import lru_cache

from fastapi import Depends, FastAPI

from heatops.config import Settings, get_settings
from heatops.domain import HeatmapFeatureCollection, HeatmapRequest
from heatops.providers.base import TemperatureProvider
from heatops.providers.mock import MockTemperatureProvider
from heatops.risk.context import SyntheticRiskContextProvider
from heatops.risk.engine import RiskEngine
from heatops.risk.models import RiskMapRequest, RiskMapResponse

app = FastAPI(
    title="HeatOps API",
    version="0.1.0",
    description="Explainable urban heat-response decision support.",
)


@lru_cache
def build_provider() -> TemperatureProvider:
    settings: Settings = get_settings()
    return MockTemperatureProvider(grid_size=settings.heatops_mock_grid_size)


def get_provider() -> TemperatureProvider:
    return build_provider()


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/heatmaps", response_model=HeatmapFeatureCollection)
async def create_heatmap(
    request: HeatmapRequest,
    provider: TemperatureProvider = Depends(get_provider),
) -> HeatmapFeatureCollection:
    return await provider.create_heatmap(request)


@app.post("/api/v1/risk-maps", response_model=RiskMapResponse)
async def create_risk_map(
    request: RiskMapRequest,
    provider: TemperatureProvider = Depends(get_provider),
) -> RiskMapResponse:
    heatmap = await provider.create_heatmap(request.heatmap)
    contexts = SyntheticRiskContextProvider().create_context(heatmap)
    return RiskEngine().assess(
        heatmap=heatmap,
        contexts=contexts,
        weights=request.weights,
        threshold_c=request.heatmap.threshold_c,
    )

