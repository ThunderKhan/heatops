from __future__ import annotations

from heatops.optimization.models import CandidateSite
from heatops.risk.models import RiskFeature, RiskMapResponse


class CellCentroidCandidateProvider:
    """Create development-only candidate sites at risk-cell centroids."""

    def create_candidates(self, risk_map: RiskMapResponse) -> tuple[CandidateSite, ...]:
        candidates = [self._candidate_for(feature) for feature in risk_map.features]
        return tuple(sorted(candidates, key=lambda candidate: candidate.site_id))

    @staticmethod
    def _candidate_for(feature: RiskFeature) -> CandidateSite:
        geometry = feature.geometry
        if geometry.get("type") != "Polygon":
            raise ValueError("candidate generation requires Polygon risk features")

        rings = geometry.get("coordinates")
        if not isinstance(rings, list) or not rings or not isinstance(rings[0], list):
            raise ValueError("risk feature has invalid Polygon coordinates")

        ring = rings[0]
        if len(ring) < 4:
            raise ValueError("risk feature Polygon must contain at least four coordinates")

        vertices = ring[:-1] if ring[0] == ring[-1] else ring
        if not vertices:
            raise ValueError("risk feature Polygon has no usable vertices")

        try:
            longitude = sum(float(point[0]) for point in vertices) / len(vertices)
            latitude = sum(float(point[1]) for point in vertices) / len(vertices)
        except (IndexError, TypeError, ValueError) as error:
            raise ValueError("risk feature contains invalid coordinate values") from error

        cell_id = feature.properties.cell_id
        return CandidateSite(
            site_id=f"candidate-{cell_id}",
            source_cell_id=cell_id,
            longitude=round(longitude, 8),
            latitude=round(latitude, 8),
            source="cell_centroid",
        )

