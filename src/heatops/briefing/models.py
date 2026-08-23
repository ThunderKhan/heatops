from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from heatops.optimization.models import PlacementRequest, PlacementResponse


class BriefNarrative(BaseModel):
    model_config = ConfigDict(frozen=True)

    headline: str = Field(min_length=1, max_length=120)
    situation_summary: str = Field(min_length=1, max_length=700)
    deployment_actions: tuple[str, ...] = Field(min_length=1, max_length=10)
    watch_items: tuple[str, ...] = Field(min_length=1, max_length=6)
    limitations: tuple[str, ...] = Field(min_length=1, max_length=6)


class ActionBrief(BriefNarrative):
    source: Literal["template", "groq"]
    model: str | None = None
    evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    grounded: Literal[True] = True


class DecisionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    placement: PlacementResponse
    brief: ActionBrief


class DecisionRequest(PlacementRequest):
    prefer_ai_brief: bool = True
