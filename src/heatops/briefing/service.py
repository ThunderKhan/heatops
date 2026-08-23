from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from heatops.briefing.evidence import create_evidence, evidence_fingerprint
from heatops.briefing.models import ActionBrief, BriefNarrative
from heatops.optimization.models import PlacementResponse


class BriefNarrator(Protocol):
    async def narrate(self, evidence: dict[str, Any]) -> BriefNarrative:
        ...


class TemplateBriefNarrator:
    async def narrate(self, evidence: dict[str, Any]) -> BriefNarrative:
        optimized = evidence["optimized"]
        baseline = evidence["baseline"]
        improvement = evidence["improvement_percentage_points"]
        actions = tuple(
            (
                f"Priority {placement['priority']}: deploy at cell "
                f"{placement['source_cell_id']} to newly reach "
                f"{placement['newly_covered_cell_count']} modeled cells."
            )
            for placement in evidence["placements"]
        )
        provenance = (
            "This run uses synthetic inputs and must be replaced or confirmed with verified data."
            if evidence["synthetic"]
            else (
                "This run uses FortyGuard heat data; vulnerability and access layers require "
                "separate provenance review."
            )
        )
        return BriefNarrative(
            headline=f"Deploy {optimized['selected_resource_count']} cooling points by priority",
            situation_summary=(
                f"The optimized plan reaches {optimized['covered_cell_count']} cells and "
                f"{optimized['covered_risk_percent']:.1f}% of modeled risk, compared with "
                f"{baseline['covered_risk_percent']:.1f}% for the naive baseline—an improvement "
                f"of {improvement:.1f} percentage points under the same resource constraint."
            ),
            deployment_actions=actions or ("No feasible deployment site was selected.",),
            watch_items=(
                "Re-run the plan if resource count, service radius, or heat conditions change.",
                "Confirm each centroid is a feasible, publicly accessible operating location.",
            ),
            limitations=(
                provenance,
                "Risk coverage is a prioritization proxy, not an estimate of illnesses or "
                "lives saved.",
            ),
        )


class GroqBriefNarrator:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout_seconds: float = 20.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Groq API key must not be blank")
        self.model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._client = client

    async def narrate(self, evidence: dict[str, Any]) -> BriefNarrative:
        if self._client is not None:
            return await self._narrate(evidence, self._client)
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            return await self._narrate(evidence, client)

    async def _narrate(
        self,
        evidence: dict[str, Any],
        client: httpx.AsyncClient,
    ) -> BriefNarrative:
        response = await client.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0.2,
                "max_completion_tokens": 900,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an urban heat incident-room analyst. Use only the supplied "
                            "evidence. Never invent locations, effects, causal claims, people, "
                            "weather, or health outcomes. Return JSON with exactly these keys: "
                            "headline, situation_summary, deployment_actions, watch_items, "
                            "limitations. The final three values must be arrays of concise strings."
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Create an operational action brief from this evidence:\n"
                        + json.dumps(evidence, sort_keys=True),
                    },
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
            return BriefNarrative.model_validate_json(content)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise RuntimeError("Groq returned an invalid action brief") from error


class BriefingService:
    def __init__(
        self,
        template: TemplateBriefNarrator,
        ai: GroqBriefNarrator | None = None,
    ) -> None:
        self._template = template
        self._ai = ai

    async def create_brief(
        self,
        plan: PlacementResponse,
        prefer_ai: bool = True,
    ) -> ActionBrief:
        evidence = create_evidence(plan)
        fingerprint = evidence_fingerprint(evidence)
        if prefer_ai and self._ai is not None:
            try:
                narrative = await self._ai.narrate(evidence)
                return ActionBrief(
                    **narrative.model_dump(),
                    source="groq",
                    model=self._ai.model,
                    evidence_fingerprint=fingerprint,
                )
            except (httpx.HTTPError, RuntimeError, ValueError):
                pass
        narrative = await self._template.narrate(evidence)
        return ActionBrief(
            **narrative.model_dump(),
            source="template",
            evidence_fingerprint=fingerprint,
        )
