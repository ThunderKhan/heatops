from __future__ import annotations

import hashlib
import json
from typing import Any

from heatops.optimization.models import PlacementResponse


def create_evidence(plan: PlacementResponse) -> dict[str, Any]:
    critical_cells = sorted(
        (
            feature
            for feature in plan.risk_map.features
            if feature.properties.risk_level.value in {"high", "critical"}
        ),
        key=lambda feature: (-feature.properties.risk_score, feature.properties.cell_id),
    )[:8]
    return {
        "algorithm": plan.algorithm,
        "synthetic": plan.synthetic,
        "coverage_radius_km": plan.coverage_radius_km,
        "optimized": {
            "selected_resource_count": plan.optimized.selected_resource_count,
            "covered_cell_count": plan.optimized.covered_cell_count,
            "covered_risk_percent": plan.optimized.covered_risk_percent,
        },
        "baseline": {
            "covered_cell_count": plan.baseline.covered_cell_count,
            "covered_risk_percent": plan.baseline.covered_risk_percent,
        },
        "improvement_percentage_points": plan.improvement_percentage_points,
        "placements": [
            {
                "priority": placement.order,
                "site_id": placement.site.site_id,
                "source_cell_id": placement.site.source_cell_id,
                "latitude": placement.site.latitude,
                "longitude": placement.site.longitude,
                "newly_covered_cell_count": len(placement.newly_covered_cell_ids),
                "newly_covered_cell_ids": list(placement.newly_covered_cell_ids),
                "marginal_covered_risk": placement.marginal_covered_risk,
            }
            for placement in plan.optimized.placements
        ],
        "highest_priority_cells": [
            {
                "cell_id": feature.properties.cell_id,
                "risk_score": feature.properties.risk_score,
                "risk_level": feature.properties.risk_level.value,
                "heat_value": feature.properties.heat_value,
                "heat_unit": feature.properties.heat_unit,
            }
            for feature in critical_cells
        ],
    }


def evidence_fingerprint(evidence: dict[str, Any]) -> str:
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
