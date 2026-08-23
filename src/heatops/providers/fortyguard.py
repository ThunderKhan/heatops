from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from time import monotonic
from typing import Any

import httpx

from heatops.domain import (
    FeatureProperties,
    GeoJsonFeature,
    HeatmapFeatureCollection,
    HeatmapRequest,
    HeatMetric,
)


class FortyGuardError(RuntimeError):
    """Raised when FortyGuard cannot return a valid heatmap."""


class FortyGuardTemperatureProvider:
    """Submit and poll FortyGuard's asynchronous Temperature API."""

    _ANALYTIC_TYPE = {
        HeatMetric.SNAPSHOT: "tcm",
        HeatMetric.EXCEEDANCE: "exceedance",
        HeatMetric.PERSISTENCE: "persistence",
    }
    _VALUE_KEYS = {
        HeatMetric.SNAPSHOT: (
            "temperature",
            "temperature_c",
            "temperature_value",
            "temp",
            "temp_c",
            "tcm",
            "value",
            "mean_temperature",
            "avg_temperature",
        ),
        HeatMetric.EXCEEDANCE: ("exceedance", "exceedance_hours", "hours", "value"),
        HeatMetric.PERSISTENCE: ("persistence", "persistence_hours", "hours", "value"),
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.fortyguard.com",
        timeout_seconds: float = 45.0,
        poll_interval_seconds: float = 1.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("FortyGuard API key must not be blank")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._client = client

    async def create_heatmap(self, request: HeatmapRequest) -> HeatmapFeatureCollection:
        if self._client is not None:
            return await self._create_heatmap(request, self._client)
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            return await self._create_heatmap(request, client)

    async def _create_heatmap(
        self,
        request: HeatmapRequest,
        client: httpx.AsyncClient,
    ) -> HeatmapFeatureCollection:
        headers = {"api-key": self._api_key, "Content-Type": "application/json"}
        submission = await client.post(
            f"{self._base_url}/v1/heatmap",
            headers=headers,
            json=self._payload(request),
        )
        self._raise_for_status(submission, "submit heatmap")
        activity_id = self._activity_id(submission.json())

        deadline = monotonic() + self._timeout_seconds
        while monotonic() < deadline:
            status_response = await client.get(
                f"{self._base_url}/v1/status/{activity_id}",
                headers={"api-key": self._api_key},
            )
            self._raise_for_status(status_response, "check heatmap status")
            payload = status_response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, dict):
                raise FortyGuardError("FortyGuard status response omitted data")
            status = str(data.get("status", "")).lower()
            if status in {"completed", "succeeded"}:
                result = data.get("result")
                if not isinstance(result, dict):
                    raise FortyGuardError("completed FortyGuard activity omitted result")
                return self._convert_map_data(result.get("map_data"), request)
            if status in {"failed", "error", "cancelled"}:
                message = payload.get("message", status) if isinstance(payload, dict) else status
                raise FortyGuardError(f"FortyGuard activity failed: {message}")
            await asyncio.sleep(self._poll_interval_seconds)

        raise FortyGuardError("FortyGuard heatmap timed out before completion")

    @staticmethod
    def _raise_for_status(response: httpx.Response, operation: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise FortyGuardError(
                f"FortyGuard could not {operation} (HTTP {response.status_code})"
            ) from error

    @staticmethod
    def _activity_id(payload: Any) -> str:
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            raise FortyGuardError("FortyGuard submission response omitted data")
        activity_id = payload["data"].get("activity_id")
        if not isinstance(activity_id, str) or not activity_id:
            raise FortyGuardError("FortyGuard submission response omitted activity_id")
        return activity_id

    def _payload(self, request: HeatmapRequest) -> dict[str, Any]:
        bounds = request.bounds
        polygon = [[
            [bounds.west, bounds.south],
            [bounds.east, bounds.south],
            [bounds.east, bounds.north],
            [bounds.west, bounds.north],
            [bounds.west, bounds.south],
        ]]
        now = datetime.now(UTC)
        selected_date = request.start_date or now.date()
        selected_time = request.start_time_utc or f"{now.hour:02d}:00"
        date_time: dict[str, Any]
        if request.metric is HeatMetric.SNAPSHOT:
            date_time = {
                "start_date": selected_date.isoformat(),
                "start_time": selected_time,
                "filter_type": 1,
            }
        else:
            date_time = {"start_date": selected_date.isoformat(), "filter_type": 3}

        payload: dict[str, Any] = {
            "polygon_aoi": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "Polygon", "coordinates": polygon},
                }],
            },
            "date_time": date_time,
            "granularity": request.granularity_m,
            "analytic_type": self._ANALYTIC_TYPE[request.metric],
        }
        if request.metric is not HeatMetric.SNAPSHOT:
            payload.update({"threshold": request.threshold_c, "direction": "above"})
        return payload

    def _convert_map_data(
        self,
        map_data: Any,
        request: HeatmapRequest,
    ) -> HeatmapFeatureCollection:
        if isinstance(map_data, str):
            try:
                map_data = json.loads(map_data)
            except json.JSONDecodeError as error:
                raise FortyGuardError("FortyGuard map_data was not valid JSON") from error
        map_data = self._find_feature_collection(map_data)
        features = map_data.get("features") if map_data is not None else None
        if not isinstance(features, list) or not features:
            raise FortyGuardError("FortyGuard map_data omitted GeoJSON features")

        converted: list[GeoJsonFeature] = []
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                raise FortyGuardError("FortyGuard map_data contained an invalid feature")
            geometry = feature.get("geometry")
            properties = feature.get("properties")
            if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
                raise FortyGuardError("FortyGuard heatmap features must be Polygon geometry")
            if not isinstance(properties, dict):
                properties = {}
            converted.append(
                GeoJsonFeature(
                    geometry=geometry,
                    properties=FeatureProperties(
                        cell_id=str(
                            properties.get("cell_id")
                            or properties.get("id")
                            or f"fortyguard-{index:04d}"
                        ),
                        metric=request.metric,
                        value=self._extract_value(properties, request.metric),
                        unit=request.metric.unit,
                        source="fortyguard",
                        threshold_c=(
                            None if request.metric is HeatMetric.SNAPSHOT else request.threshold_c
                        ),
                    ),
                )
            )
        return HeatmapFeatureCollection(features=tuple(converted), synthetic=False)

    @classmethod
    def _find_feature_collection(cls, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            if isinstance(value.get("features"), list):
                return value
            for child in value.values():
                found = cls._find_feature_collection(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._find_feature_collection(child)
                if found is not None:
                    return found
        return None

    def _extract_value(self, properties: dict[str, Any], metric: HeatMetric) -> float:
        lowered = self._flatten_properties(properties)
        for key in self._VALUE_KEYS[metric]:
            value = lowered.get(key)
            if isinstance(value, int | float) and not isinstance(value, bool):
                return max(0.0, float(value))
        numeric = [
            float(value)
            for key, value in lowered.items()
            if isinstance(value, int | float)
            and not isinstance(value, bool)
            and key not in {"id", "index", "latitude", "longitude", "lat", "lon"}
        ]
        if len(numeric) == 1:
            return max(0.0, numeric[0])
        raise FortyGuardError("FortyGuard heatmap feature omitted a recognized metric value")

    @classmethod
    def _flatten_properties(
        cls,
        properties: dict[str, Any],
        prefix: str = "",
    ) -> dict[str, Any]:
        flattened: dict[str, Any] = {}
        for key, value in properties.items():
            normalized = str(key).lower()
            path = f"{prefix}.{normalized}" if prefix else normalized
            flattened[normalized] = value
            flattened[path] = value
            if isinstance(value, dict):
                flattened.update(cls._flatten_properties(value, path))
        return flattened
