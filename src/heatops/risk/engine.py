from __future__ import annotations

from collections import Counter

from heatops.domain import HeatmapFeatureCollection, HeatMetric
from heatops.risk.models import (
    RiskComputation,
    RiskContext,
    RiskFeature,
    RiskLevel,
    RiskMapResponse,
    RiskProperties,
    RiskSummary,
    RiskWeights,
)


class RiskEngine:
    """Calculate deterministic and inspectable heat-priority scores."""

    def assess(
        self,
        heatmap: HeatmapFeatureCollection,
        contexts: tuple[RiskContext, ...],
        weights: RiskWeights,
        threshold_c: float,
    ) -> RiskMapResponse:
        context_by_id = self._index_context(contexts)
        heat_ids = [feature.properties.cell_id for feature in heatmap.features]
        if len(set(heat_ids)) != len(heat_ids):
            raise ValueError("heatmap contains duplicate cell identifiers")

        missing = sorted(set(heat_ids) - context_by_id.keys())
        if missing:
            raise ValueError(f"missing risk context for cells: {', '.join(missing[:5])}")

        risk_features: list[RiskFeature] = []
        for feature in heatmap.features:
            heat = feature.properties
            context = context_by_id[heat.cell_id]
            hazard = self.normalize_hazard(
                metric=heat.metric,
                value=heat.value,
                threshold_c=threshold_c,
            )
            computation = self.calculate_score(hazard, context, weights)
            risk_features.append(
                RiskFeature(
                    geometry=feature.geometry,
                    properties=RiskProperties(
                        cell_id=heat.cell_id,
                        heat_metric=heat.metric,
                        heat_value=heat.value,
                        heat_unit=heat.unit,
                        heat_threshold_c=threshold_c,
                        hazard=computation.hazard,
                        exposure=context.exposure,
                        vulnerability=context.vulnerability,
                        cooling_access=context.cooling_access,
                        lack_of_access=computation.lack_of_access,
                        exposure_contribution=computation.exposure_contribution,
                        vulnerability_contribution=computation.vulnerability_contribution,
                        access_contribution=computation.access_contribution,
                        risk_score=computation.score,
                        risk_level=computation.level,
                        heat_source=heat.source,
                        context_source=context.source,
                    ),
                )
            )

        summary = self._summarize(risk_features)
        is_synthetic = heatmap.synthetic or any(
            context.source == "synthetic" for context in contexts
        )
        return RiskMapResponse(
            features=tuple(risk_features),
            weights=weights,
            summary=summary,
            synthetic=is_synthetic,
        )

    @staticmethod
    def normalize_hazard(metric: HeatMetric, value: float, threshold_c: float) -> float:
        if metric is HeatMetric.SNAPSHOT:
            lower, upper = threshold_c - 5.0, threshold_c + 5.0
        elif metric is HeatMetric.EXCEEDANCE:
            lower, upper = 0.0, 12.0
        else:
            lower, upper = 0.0, 8.0

        return round(RiskEngine._clamp((value - lower) / (upper - lower)), 6)

    @staticmethod
    def calculate_score(
        hazard: float,
        context: RiskContext,
        weights: RiskWeights,
    ) -> RiskComputation:
        hazard = RiskEngine._clamp(hazard)
        lack_of_access = 1.0 - context.cooling_access
        exposure_contribution = hazard * weights.exposure * context.exposure
        vulnerability_contribution = hazard * weights.vulnerability * context.vulnerability
        access_contribution = hazard * weights.lack_of_access * lack_of_access
        score = exposure_contribution + vulnerability_contribution + access_contribution

        return RiskComputation(
            hazard=round(hazard, 6),
            lack_of_access=round(lack_of_access, 6),
            exposure_contribution=round(exposure_contribution, 6),
            vulnerability_contribution=round(vulnerability_contribution, 6),
            access_contribution=round(access_contribution, 6),
            score=round(score, 6),
            level=RiskEngine.classify(score),
        )

    @staticmethod
    def classify(score: float) -> RiskLevel:
        if score >= 0.75:
            return RiskLevel.CRITICAL
        if score >= 0.50:
            return RiskLevel.HIGH
        if score >= 0.25:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    @staticmethod
    def _index_context(contexts: tuple[RiskContext, ...]) -> dict[str, RiskContext]:
        indexed = {context.cell_id: context for context in contexts}
        if len(indexed) != len(contexts):
            raise ValueError("risk context contains duplicate cell identifiers")
        return indexed

    @staticmethod
    def _summarize(features: list[RiskFeature]) -> RiskSummary:
        if not features:
            return RiskSummary(
                cell_count=0,
                mean_score=0.0,
                maximum_score=0.0,
                level_counts={level: 0 for level in RiskLevel},
            )

        scores = [feature.properties.risk_score for feature in features]
        counts = Counter(feature.properties.risk_level for feature in features)
        return RiskSummary(
            cell_count=len(features),
            mean_score=round(sum(scores) / len(scores), 6),
            maximum_score=max(scores),
            level_counts={level: counts[level] for level in RiskLevel},
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return min(1.0, max(0.0, value))
