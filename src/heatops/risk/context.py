from __future__ import annotations

import hashlib

from heatops.domain import HeatmapFeatureCollection
from heatops.risk.models import RiskContext


class SyntheticRiskContextProvider:
    """Create deterministic development-only exposure and vulnerability values."""

    def create_context(self, heatmap: HeatmapFeatureCollection) -> tuple[RiskContext, ...]:
        return tuple(self._context_for(feature.properties.cell_id) for feature in heatmap.features)

    @staticmethod
    def _context_for(cell_id: str) -> RiskContext:
        coordinates = SyntheticRiskContextProvider._mock_coordinates(cell_id)
        if coordinates is not None:
            row, column = coordinates
            exposure = min(1.0, 0.35 + 0.07 * row + 0.025 * column)
            vulnerability = min(1.0, 0.35 + 0.06 * column + 0.015 * ((row + column) % 4))
            cooling_access = min(1.0, 0.10 + 0.08 * ((3 * row + 2 * column) % 8))
        else:
            digest = hashlib.sha256(cell_id.encode("utf-8")).digest()
            exposure = 0.20 + 0.75 * digest[0] / 255
            vulnerability = 0.15 + 0.80 * digest[1] / 255
            cooling_access = 0.05 + 0.85 * digest[2] / 255

        return RiskContext(
            cell_id=cell_id,
            exposure=round(exposure, 6),
            vulnerability=round(vulnerability, 6),
            cooling_access=round(cooling_access, 6),
            source="synthetic",
        )

    @staticmethod
    def _mock_coordinates(cell_id: str) -> tuple[int, int] | None:
        parts = cell_id.split("-")
        if len(parts) != 3 or parts[0] != "mock":
            return None
        try:
            return int(parts[1]), int(parts[2])
        except ValueError:
            return None
