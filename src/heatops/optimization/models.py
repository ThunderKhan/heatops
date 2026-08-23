from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from heatops.risk.models import RiskMapRequest, RiskMapResponse


class CandidateSite(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_id: str
    source_cell_id: str
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    source: Literal["cell_centroid", "openstreetmap", "verified"]


class PlacementRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_map: RiskMapRequest
    resource_count: int = Field(default=5, ge=1, le=20)
    coverage_radius_km: float = Field(default=0.75, gt=0, le=20)


class SelectedPlacement(BaseModel):
    model_config = ConfigDict(frozen=True)

    order: int = Field(ge=1)
    site: CandidateSite
    newly_covered_cell_ids: tuple[str, ...]
    marginal_covered_risk: float = Field(ge=0)


class PlacementPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy: Literal["optimized", "highest_risk_baseline"]
    requested_resource_count: int = Field(ge=1)
    selected_resource_count: int = Field(ge=0)
    placements: tuple[SelectedPlacement, ...]
    covered_cell_ids: tuple[str, ...]
    covered_cell_count: int = Field(ge=0)
    total_risk_burden: float = Field(ge=0)
    covered_risk_burden: float = Field(ge=0)
    covered_risk_percent: float = Field(ge=0, le=100)


class PlacementResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_map: RiskMapResponse
    candidate_count: int = Field(ge=0)
    coverage_radius_km: float = Field(gt=0)
    optimized: PlacementPlan
    baseline: PlacementPlan
    improvement_percentage_points: float
    synthetic: bool
    algorithm: Literal["greedy_weighted_maximum_coverage_with_baseline_guard"] = (
        "greedy_weighted_maximum_coverage_with_baseline_guard"
    )

