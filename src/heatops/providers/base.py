from typing import Protocol

from heatops.domain import HeatmapFeatureCollection, HeatmapRequest


class TemperatureProvider(Protocol):
    """Boundary implemented by mock, cached, and FortyGuard providers."""

    async def create_heatmap(self, request: HeatmapRequest) -> HeatmapFeatureCollection:
        """Return a validated heatmap for the requested bounds and metric."""
        ...

