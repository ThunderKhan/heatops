from __future__ import annotations

import math

from heatops.optimization.models import (
    CandidateSite,
    PlacementPlan,
    PlacementResponse,
    SelectedPlacement,
)
from heatops.risk.models import RiskMapResponse


class PlacementOptimizer:
    """Deterministic greedy weighted maximum-coverage optimizer."""

    EARTH_RADIUS_KM = 6371.0088

    def optimize(
        self,
        risk_map: RiskMapResponse,
        candidates: tuple[CandidateSite, ...],
        resource_count: int,
        coverage_radius_km: float,
    ) -> PlacementResponse:
        if resource_count < 1:
            raise ValueError("resource_count must be at least one")
        if coverage_radius_km <= 0:
            raise ValueError("coverage_radius_km must be positive")
        if not candidates:
            raise ValueError("at least one candidate site is required")

        risk_by_cell = self._risk_by_cell(risk_map)
        centroids = self._risk_centroids(risk_map)
        coverage = self._coverage_sets(candidates, centroids, coverage_radius_km)
        limit = min(resource_count, len(candidates))

        greedy_ids = self._greedy_selection(candidates, coverage, risk_by_cell, limit)
        baseline_ids = self._baseline_selection(candidates, risk_by_cell, limit)
        greedy_plan = self._build_plan(
            "optimized", greedy_ids, candidates, coverage, risk_by_cell, resource_count
        )
        baseline_plan = self._build_plan(
            "highest_risk_baseline",
            baseline_ids,
            candidates,
            coverage,
            risk_by_cell,
            resource_count,
        )

        if greedy_plan.covered_risk_burden + 1e-9 < baseline_plan.covered_risk_burden:
            optimized_plan = self._build_plan(
                "optimized", baseline_ids, candidates, coverage, risk_by_cell, resource_count
            )
        else:
            optimized_plan = greedy_plan

        return PlacementResponse(
            risk_map=risk_map,
            candidate_count=len(candidates),
            coverage_radius_km=coverage_radius_km,
            optimized=optimized_plan,
            baseline=baseline_plan,
            improvement_percentage_points=round(
                optimized_plan.covered_risk_percent - baseline_plan.covered_risk_percent,
                6,
            ),
            synthetic=risk_map.synthetic
            or any(candidate.source == "cell_centroid" for candidate in candidates),
        )

    @staticmethod
    def _risk_by_cell(risk_map: RiskMapResponse) -> dict[str, float]:
        risk_by_cell = {
            feature.properties.cell_id: feature.properties.risk_score
            for feature in risk_map.features
        }
        if len(risk_by_cell) != len(risk_map.features):
            raise ValueError("risk map contains duplicate cell identifiers")
        return risk_by_cell

    @staticmethod
    def _risk_centroids(risk_map: RiskMapResponse) -> dict[str, tuple[float, float]]:
        centroids: dict[str, tuple[float, float]] = {}
        for feature in risk_map.features:
            candidate = CellGeometry.centroid(feature.geometry)
            centroids[feature.properties.cell_id] = candidate
        return centroids

    def _coverage_sets(
        self,
        candidates: tuple[CandidateSite, ...],
        centroids: dict[str, tuple[float, float]],
        radius_km: float,
    ) -> dict[str, frozenset[str]]:
        coverage: dict[str, frozenset[str]] = {}
        for candidate in candidates:
            covered = {
                cell_id
                for cell_id, (longitude, latitude) in centroids.items()
                if self.haversine_km(
                    candidate.longitude,
                    candidate.latitude,
                    longitude,
                    latitude,
                )
                <= radius_km + 1e-9
            }
            coverage[candidate.site_id] = frozenset(covered)
        return coverage

    @staticmethod
    def _greedy_selection(
        candidates: tuple[CandidateSite, ...],
        coverage: dict[str, frozenset[str]],
        risk_by_cell: dict[str, float],
        limit: int,
    ) -> tuple[str, ...]:
        available = {candidate.site_id for candidate in candidates}
        covered: set[str] = set()
        selected: list[str] = []

        while available and len(selected) < limit:
            def marginal_gain(site_id: str) -> float:
                return sum(risk_by_cell[cell] for cell in coverage[site_id] - covered)

            site_id = min(available, key=lambda item: (-marginal_gain(item), item))
            if marginal_gain(site_id) <= 1e-12:
                break
            selected.append(site_id)
            covered.update(coverage[site_id])
            available.remove(site_id)

        return tuple(selected)

    @staticmethod
    def _baseline_selection(
        candidates: tuple[CandidateSite, ...],
        risk_by_cell: dict[str, float],
        limit: int,
    ) -> tuple[str, ...]:
        ordered = sorted(
            candidates,
            key=lambda candidate: (
                -risk_by_cell.get(candidate.source_cell_id, 0.0),
                candidate.site_id,
            ),
        )
        return tuple(candidate.site_id for candidate in ordered[:limit])

    @staticmethod
    def _build_plan(
        strategy: str,
        selected_ids: tuple[str, ...],
        candidates: tuple[CandidateSite, ...],
        coverage: dict[str, frozenset[str]],
        risk_by_cell: dict[str, float],
        requested_count: int,
    ) -> PlacementPlan:
        candidate_by_id = {candidate.site_id: candidate for candidate in candidates}
        covered: set[str] = set()
        placements: list[SelectedPlacement] = []

        for order, site_id in enumerate(selected_ids, start=1):
            newly_covered = coverage[site_id] - covered
            marginal_risk = sum(risk_by_cell[cell] for cell in newly_covered)
            placements.append(
                SelectedPlacement(
                    order=order,
                    site=candidate_by_id[site_id],
                    newly_covered_cell_ids=tuple(sorted(newly_covered)),
                    marginal_covered_risk=round(marginal_risk, 6),
                )
            )
            covered.update(coverage[site_id])

        total_risk = sum(risk_by_cell.values())
        covered_risk = sum(risk_by_cell[cell] for cell in covered)
        percent = 0.0 if total_risk <= 1e-12 else 100.0 * covered_risk / total_risk
        return PlacementPlan(
            strategy=strategy,
            requested_resource_count=requested_count,
            selected_resource_count=len(placements),
            placements=tuple(placements),
            covered_cell_ids=tuple(sorted(covered)),
            covered_cell_count=len(covered),
            total_risk_burden=round(total_risk, 6),
            covered_risk_burden=round(covered_risk, 6),
            covered_risk_percent=round(percent, 6),
        )

    @classmethod
    def haversine_km(
        cls,
        longitude_a: float,
        latitude_a: float,
        longitude_b: float,
        latitude_b: float,
    ) -> float:
        latitude_a_rad = math.radians(latitude_a)
        latitude_b_rad = math.radians(latitude_b)
        delta_latitude = math.radians(latitude_b - latitude_a)
        delta_longitude = math.radians(longitude_b - longitude_a)
        haversine = (
            math.sin(delta_latitude / 2) ** 2
            + math.cos(latitude_a_rad)
            * math.cos(latitude_b_rad)
            * math.sin(delta_longitude / 2) ** 2
        )
        return 2 * cls.EARTH_RADIUS_KM * math.asin(math.sqrt(haversine))


class CellGeometry:
    """Small geometry helpers shared by optimization internals."""

    @staticmethod
    def centroid(geometry: dict[str, object]) -> tuple[float, float]:
        if geometry.get("type") != "Polygon":
            raise ValueError("optimization requires Polygon risk features")
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or not coordinates:
            raise ValueError("risk feature has invalid Polygon coordinates")
        ring = coordinates[0]
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError("risk feature Polygon must contain at least four coordinates")
        vertices = ring[:-1] if ring[0] == ring[-1] else ring
        try:
            longitude = sum(float(point[0]) for point in vertices) / len(vertices)
            latitude = sum(float(point[1]) for point in vertices) / len(vertices)
        except (IndexError, TypeError, ValueError) as error:
            raise ValueError("risk feature contains invalid coordinate values") from error
        return longitude, latitude
