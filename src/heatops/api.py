from functools import lru_cache

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from heatops.briefing.models import DecisionRequest, DecisionResponse
from heatops.briefing.service import BriefingService, GroqBriefNarrator, TemplateBriefNarrator
from heatops.config import Settings, get_settings
from heatops.domain import HeatmapFeatureCollection, HeatmapRequest
from heatops.optimization.candidates import CellCentroidCandidateProvider
from heatops.optimization.engine import PlacementOptimizer
from heatops.optimization.models import PlacementRequest, PlacementResponse
from heatops.providers.base import TemperatureProvider
from heatops.providers.fallback import FallbackTemperatureProvider
from heatops.providers.fortyguard import FortyGuardTemperatureProvider
from heatops.providers.mock import MockTemperatureProvider
from heatops.risk.context import SyntheticRiskContextProvider
from heatops.risk.engine import RiskEngine
from heatops.risk.models import RiskMapRequest, RiskMapResponse

app = FastAPI(
    title="HeatOps API",
    version="0.1.0",
    description="Explainable urban heat-response decision support.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@lru_cache
def build_provider() -> TemperatureProvider:
    settings: Settings = get_settings()
    mock = MockTemperatureProvider(grid_size=settings.heatops_mock_grid_size)
    if settings.heatops_provider == "mock":
        return mock
    if not settings.fortyguard_api_key:
        if settings.heatops_provider == "fortyguard":
            raise RuntimeError("FORTYGUARD_API_KEY is required for the fortyguard provider")
        return mock
    fortyguard = FortyGuardTemperatureProvider(
        api_key=settings.fortyguard_api_key,
        base_url=settings.fortyguard_base_url,
        timeout_seconds=settings.fortyguard_timeout_seconds,
        poll_interval_seconds=settings.fortyguard_poll_interval_seconds,
    )
    if settings.heatops_provider == "fortyguard":
        return fortyguard
    return FallbackTemperatureProvider(primary=fortyguard, fallback=mock)


@lru_cache
def build_briefing_service() -> BriefingService:
    settings = get_settings()
    ai = (
        GroqBriefNarrator(
            api_key=settings.groq_api_key,
            model=settings.heatops_groq_model,
            base_url=settings.groq_base_url,
            timeout_seconds=settings.groq_timeout_seconds,
        )
        if settings.groq_api_key
        else None
    )
    return BriefingService(template=TemplateBriefNarrator(), ai=ai)


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
    return await build_risk_map(request, provider)


async def build_risk_map(
    request: RiskMapRequest,
    provider: TemperatureProvider,
) -> RiskMapResponse:
    heatmap = await provider.create_heatmap(request.heatmap)
    contexts = SyntheticRiskContextProvider().create_context(heatmap)
    return RiskEngine().assess(
        heatmap=heatmap,
        contexts=contexts,
        weights=request.weights,
        threshold_c=request.heatmap.threshold_c,
    )


@app.post("/api/v1/placement-plans", response_model=PlacementResponse)
async def create_placement_plan(
    request: PlacementRequest,
    provider: TemperatureProvider = Depends(get_provider),
) -> PlacementResponse:
    return await build_placement_plan(request, provider)


async def build_placement_plan(
    request: PlacementRequest,
    provider: TemperatureProvider,
) -> PlacementResponse:
    risk_map = await build_risk_map(request.risk_map, provider)
    candidates = CellCentroidCandidateProvider().create_candidates(risk_map)
    return PlacementOptimizer().optimize(
        risk_map=risk_map,
        candidates=candidates,
        resource_count=request.resource_count,
        coverage_radius_km=request.coverage_radius_km,
    )


@app.post("/api/v1/decisions", response_model=DecisionResponse)
async def create_decision(
    request: DecisionRequest,
    provider: TemperatureProvider = Depends(get_provider),
) -> DecisionResponse:
    placement = await build_placement_plan(request, provider)
    brief = await build_briefing_service().create_brief(
        placement,
        prefer_ai=request.prefer_ai_brief,
    )
    return DecisionResponse(placement=placement, brief=brief)
