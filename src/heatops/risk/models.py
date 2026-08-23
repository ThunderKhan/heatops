from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from heatops.domain import HeatmapRequest, HeatMetric


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskWeights(BaseModel):
    model_config = ConfigDict(frozen=True)

    exposure: float = Field(default=0.35, ge=0, le=1)
    vulnerability: float = Field(default=0.40, ge=0, le=1)
    lack_of_access: float = Field(default=0.25, ge=0, le=1)

    @model_validator(mode="after")
    def require_unit_sum(self) -> "RiskWeights":
        total = self.exposure + self.vulnerability + self.lack_of_access
        if abs(total - 1.0) > 1e-9:
            raise ValueError("risk weights must sum to 1.0")
        return self


class RiskContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell_id: str
    exposure: float = Field(ge=0, le=1)
    vulnerability: float = Field(ge=0, le=1)
    cooling_access: float = Field(ge=0, le=1)
    source: Literal["synthetic", "open_data", "verified"]


class RiskComputation(BaseModel):
    model_config = ConfigDict(frozen=True)

    hazard: float = Field(ge=0, le=1)
    lack_of_access: float = Field(ge=0, le=1)
    exposure_contribution: float = Field(ge=0, le=1)
    vulnerability_contribution: float = Field(ge=0, le=1)
    access_contribution: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)
    level: RiskLevel


class RiskMapRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    heatmap: HeatmapRequest
    weights: RiskWeights = Field(default_factory=RiskWeights)


class RiskProperties(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell_id: str
    heat_metric: HeatMetric
    heat_value: float
    heat_unit: Literal["celsius", "hours"]
    heat_threshold_c: float
    hazard: float = Field(ge=0, le=1)
    exposure: float = Field(ge=0, le=1)
    vulnerability: float = Field(ge=0, le=1)
    cooling_access: float = Field(ge=0, le=1)
    lack_of_access: float = Field(ge=0, le=1)
    exposure_contribution: float = Field(ge=0, le=1)
    vulnerability_contribution: float = Field(ge=0, le=1)
    access_contribution: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    heat_source: Literal["synthetic", "fortyguard", "cache"]
    context_source: Literal["synthetic", "open_data", "verified"]


class RiskFeature(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: RiskProperties


class RiskSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell_count: int = Field(ge=0)
    mean_score: float = Field(ge=0, le=1)
    maximum_score: float = Field(ge=0, le=1)
    level_counts: dict[RiskLevel, int]


class RiskMapResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: tuple[RiskFeature, ...]
    weights: RiskWeights
    summary: RiskSummary
    synthetic: bool
    formula: Literal["H * (wE*E + wV*V + wA*(1-C))"] = (
        "H * (wE*E + wV*V + wA*(1-C))"
    )
