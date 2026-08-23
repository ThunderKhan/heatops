from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HeatMetric(StrEnum):
    SNAPSHOT = "snapshot"
    EXCEEDANCE = "exceedance"
    PERSISTENCE = "persistence"

    @property
    def unit(self) -> str:
        return "celsius" if self is HeatMetric.SNAPSHOT else "hours"


class GeoBounds(BaseModel):
    model_config = ConfigDict(frozen=True)

    north: float = Field(le=90)
    south: float = Field(ge=-90)
    east: float = Field(le=180)
    west: float = Field(ge=-180)

    @model_validator(mode="after")
    def validate_order(self) -> "GeoBounds":
        if self.north <= self.south:
            raise ValueError("north must be greater than south")
        if self.east <= self.west:
            raise ValueError("east must be greater than west; antimeridian AOIs are unsupported")
        return self


class HeatmapRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    bounds: GeoBounds
    metric: HeatMetric = HeatMetric.SNAPSHOT
    threshold_c: float = Field(default=35.0, ge=-20, le=70)


class FeatureProperties(BaseModel):
    model_config = ConfigDict(frozen=True)

    cell_id: str
    metric: HeatMetric
    value: float = Field(ge=0)
    unit: Literal["celsius", "hours"]
    source: Literal["synthetic", "fortyguard", "cache"]
    threshold_c: float | None = None


class GeoJsonFeature(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: FeatureProperties


class HeatmapFeatureCollection(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: tuple[GeoJsonFeature, ...]
    synthetic: bool

