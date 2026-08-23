from heatops.domain import HeatmapFeatureCollection, HeatmapRequest
from heatops.providers.base import TemperatureProvider


class FallbackTemperatureProvider:
    """Use a clearly-labelled synthetic provider when the remote provider is unavailable."""

    def __init__(
        self,
        primary: TemperatureProvider,
        fallback: TemperatureProvider,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    async def create_heatmap(self, request: HeatmapRequest) -> HeatmapFeatureCollection:
        try:
            return await self._primary.create_heatmap(request)
        except Exception:
            return await self._fallback.create_heatmap(request)
