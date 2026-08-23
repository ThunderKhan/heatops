from __future__ import annotations

import math

from heatops.domain import (
    FeatureProperties,
    GeoJsonFeature,
    HeatmapFeatureCollection,
    HeatmapRequest,
    HeatMetric,
)


class MockTemperatureProvider:
    """Generate deterministic synthetic cells for development and demonstrations."""

    def __init__(self, grid_size: int = 8) -> None:
        if not 2 <= grid_size <= 50:
            raise ValueError("grid_size must be between 2 and 50")
        self._grid_size = grid_size

    async def create_heatmap(self, request: HeatmapRequest) -> HeatmapFeatureCollection:
        bounds = request.bounds
        lat_step = (bounds.north - bounds.south) / self._grid_size
        lon_step = (bounds.east - bounds.west) / self._grid_size
        features: list[GeoJsonFeature] = []

        for row in range(self._grid_size):
            for column in range(self._grid_size):
                south = bounds.south + row * lat_step
                north = south + lat_step
                west = bounds.west + column * lon_step
                east = west + lon_step
                temperature_c = self._temperature(row, column)
                value = self._metric_value(request, temperature_c, row, column)

                features.append(
                    GeoJsonFeature(
                        geometry={
                            "type": "Polygon",
                            "coordinates": [[
                                [west, south],
                                [east, south],
                                [east, north],
                                [west, north],
                                [west, south],
                            ]],
                        },
                        properties=FeatureProperties(
                            cell_id=f"mock-{row:02d}-{column:02d}",
                            metric=request.metric,
                            value=value,
                            unit=request.metric.unit,
                            source="synthetic",
                            threshold_c=(
                                None
                                if request.metric is HeatMetric.SNAPSHOT
                                else request.threshold_c
                            ),
                        ),
                    )
                )

        return HeatmapFeatureCollection(features=tuple(features), synthetic=True)

    def _temperature(self, row: int, column: int) -> float:
        centre = (self._grid_size - 1) / 2
        distance = math.hypot(row - centre, column - centre)
        hotspot = max(0.0, 5.4 - 0.9 * distance)
        east_west_effect = 0.22 * column
        return round(31.8 + hotspot + east_west_effect, 2)

    @staticmethod
    def _metric_value(
        request: HeatmapRequest,
        temperature_c: float,
        row: int,
        column: int,
    ) -> float:
        if request.metric is HeatMetric.SNAPSHOT:
            return temperature_c

        degrees_over = max(0.0, temperature_c - request.threshold_c)
        exceedance_hours = min(24.0, round(degrees_over * 2.6 + (row + column) % 3, 2))

        if request.metric is HeatMetric.EXCEEDANCE:
            return exceedance_hours

        continuity_factor = 0.55 + 0.05 * ((row * 3 + column) % 5)
        return round(min(exceedance_hours, exceedance_hours * continuity_factor), 2)

