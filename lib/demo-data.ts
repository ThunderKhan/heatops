import type {
  CandidateSite,
  DecisionResponse,
  HeatMetric,
  PlacementPlan,
  PlacementResponse,
  RiskFeature,
  RiskLevel,
} from "@/lib/types";

const BOUNDS = { north: 28.755, south: 28.705, east: -81.315, west: -81.375 };
const GRID_SIZE = 8;
const OPTIMIZED_CELLS = [
  "mock-04-05",
  "mock-03-03",
  "mock-06-06",
  "mock-02-06",
  "mock-06-03",
  "mock-01-02",
  "mock-05-01",
  "mock-01-07",
  "mock-07-04",
  "mock-03-07",
];
const BASELINE_CELLS = [
  "mock-03-04",
  "mock-04-06",
  "mock-05-05",
  "mock-04-05",
  "mock-05-06",
  "mock-02-03",
  "mock-06-05",
  "mock-02-05",
  "mock-06-04",
  "mock-01-04",
];

function clamp(value: number) {
  return Math.min(1, Math.max(0, value));
}

function riskLevel(score: number): RiskLevel {
  if (score >= 0.75) return "critical";
  if (score >= 0.5) return "high";
  if (score >= 0.25) return "moderate";
  return "low";
}

function createFeatures(metric: HeatMetric): RiskFeature[] {
  const latStep = (BOUNDS.north - BOUNDS.south) / GRID_SIZE;
  const lonStep = (BOUNDS.east - BOUNDS.west) / GRID_SIZE;
  const centre = (GRID_SIZE - 1) / 2;

  return Array.from({ length: GRID_SIZE * GRID_SIZE }, (_, index) => {
    const row = Math.floor(index / GRID_SIZE);
    const column = index % GRID_SIZE;
    const south = BOUNDS.south + row * latStep;
    const north = south + latStep;
    const west = BOUNDS.west + column * lonStep;
    const east = west + lonStep;
    const distance = Math.hypot(row - centre, column - centre);
    const temperature = 31.8 + Math.max(0, 5.4 - 0.9 * distance) + 0.22 * column;
    const hazard = clamp((temperature - 30) / 10);
    const exposure = clamp(0.35 + 0.07 * row + 0.025 * column);
    const vulnerability = clamp(0.35 + 0.06 * column + 0.015 * ((row + column) % 4));
    const coolingAccess = clamp(0.1 + 0.08 * ((3 * row + 2 * column) % 8));
    const lackOfAccess = 1 - coolingAccess;
    const exposureContribution = hazard * 0.35 * exposure;
    const vulnerabilityContribution = hazard * 0.4 * vulnerability;
    const accessContribution = hazard * 0.25 * lackOfAccess;
    const score = exposureContribution + vulnerabilityContribution + accessContribution;
    const cellId = `mock-${String(row).padStart(2, "0")}-${String(column).padStart(2, "0")}`;

    return {
      type: "Feature",
      geometry: {
        type: "Polygon",
        coordinates: [
          [[west, south], [east, south], [east, north], [west, north], [west, south]],
        ],
      },
      properties: {
        cell_id: cellId,
        heat_metric: metric,
        heat_value: Number(temperature.toFixed(2)),
        heat_unit: metric === "snapshot" ? "celsius" : "hours",
        heat_threshold_c: 35,
        hazard: Number(hazard.toFixed(6)),
        exposure: Number(exposure.toFixed(6)),
        vulnerability: Number(vulnerability.toFixed(6)),
        cooling_access: Number(coolingAccess.toFixed(6)),
        lack_of_access: Number(lackOfAccess.toFixed(6)),
        exposure_contribution: Number(exposureContribution.toFixed(6)),
        vulnerability_contribution: Number(vulnerabilityContribution.toFixed(6)),
        access_contribution: Number(accessContribution.toFixed(6)),
        risk_score: Number(score.toFixed(6)),
        risk_level: riskLevel(score),
        heat_source: "synthetic",
        context_source: "synthetic",
      },
    };
  });
}

function siteFor(cellId: string, features: RiskFeature[]): CandidateSite {
  const feature = features.find((item) => item.properties.cell_id === cellId) ?? features[0];
  const ring = feature.geometry.coordinates[0].slice(0, -1);
  const longitude = ring.reduce((sum, point) => sum + point[0], 0) / ring.length;
  const latitude = ring.reduce((sum, point) => sum + point[1], 0) / ring.length;
  return {
    site_id: `candidate-${cellId}`,
    source_cell_id: cellId,
    longitude,
    latitude,
    source: "cell_centroid",
  };
}

function createPlan(
  strategy: PlacementPlan["strategy"],
  cellIds: string[],
  features: RiskFeature[],
  coveredPercent: number,
  coveredCount: number,
): PlacementPlan {
  const totalRisk = features.reduce((sum, feature) => sum + feature.properties.risk_score, 0);
  return {
    strategy,
    requested_resource_count: cellIds.length,
    selected_resource_count: cellIds.length,
    placements: cellIds.map((cellId, index) => ({
      order: index + 1,
      site: siteFor(cellId, features),
      newly_covered_cell_ids: [],
      marginal_covered_risk: Number(
        ((totalRisk * coveredPercent) / 100 / cellIds.length).toFixed(6),
      ),
    })),
    covered_cell_ids: features.slice(0, coveredCount).map((feature) => feature.properties.cell_id),
    covered_cell_count: coveredCount,
    total_risk_burden: Number(totalRisk.toFixed(6)),
    covered_risk_burden: Number(((totalRisk * coveredPercent) / 100).toFixed(6)),
    covered_risk_percent: coveredPercent,
  };
}

export function createDemoResponse(
  scenario: { metric: HeatMetric; resourceCount: number; coverageRadiusKm: number } = {
    metric: "snapshot",
    resourceCount: 5,
    coverageRadiusKm: 0.75,
  },
): PlacementResponse {
  const { metric, resourceCount, coverageRadiusKm } = scenario;
  const features = createFeatures(metric);
  const counts: Record<RiskLevel, number> = { low: 0, moderate: 0, high: 0, critical: 0 };
  features.forEach((feature) => counts[feature.properties.risk_level] += 1);
  const scores = features.map((feature) => feature.properties.risk_score);

  const countFactor = 0.45 + 0.55 * (resourceCount / 5);
  const radiusFactor = 0.75 + 0.25 * (coverageRadiusKm / 0.75);
  const optimizedPercent = Math.min(86, 48.500507 * countFactor * radiusFactor);
  const baselinePercent = Math.min(78, 33.11468 * countFactor * radiusFactor);
  const optimizedCount = Math.max(1, Math.round(25 * optimizedPercent / 48.500507));
  const baselineCount = Math.max(1, Math.round(17 * baselinePercent / 33.11468));
  const optimizedSites = OPTIMIZED_CELLS.slice(0, resourceCount);
  const baselineSites = BASELINE_CELLS.slice(0, resourceCount);

  return {
    risk_map: {
      type: "FeatureCollection",
      features,
      weights: { exposure: 0.35, vulnerability: 0.4, lack_of_access: 0.25 },
      summary: {
        cell_count: features.length,
        mean_score: scores.reduce((sum, score) => sum + score, 0) / scores.length,
        maximum_score: Math.max(...scores),
        level_counts: counts,
      },
      synthetic: true,
      formula: "H * (wE*E + wV*V + wA*(1-C))",
    },
    candidate_count: 64,
    coverage_radius_km: coverageRadiusKm,
    optimized: createPlan("optimized", optimizedSites, features, optimizedPercent, optimizedCount),
    baseline: createPlan(
      "highest_risk_baseline",
      baselineSites,
      features,
      baselinePercent,
      baselineCount,
    ),
    improvement_percentage_points: optimizedPercent - baselinePercent,
    synthetic: true,
    algorithm: "greedy_weighted_maximum_coverage_with_baseline_guard",
  };
}

export function createDemoDecision(
  scenario?: { metric: HeatMetric; resourceCount: number; coverageRadiusKm: number },
): DecisionResponse {
  const placement = createDemoResponse(scenario);
  const actions = placement.optimized.placements.map(
    (item) =>
      `Priority ${item.order}: deploy at ${item.site.source_cell_id} and verify public access before activation.`,
  );
  return {
    placement,
    brief: {
      headline: `Deploy ${placement.optimized.selected_resource_count} cooling points by priority`,
      situation_summary:
        `The optimized plan covers ${placement.optimized.covered_risk_percent.toFixed(1)}% ` +
        `of modeled risk, versus ${placement.baseline.covered_risk_percent.toFixed(1)}% for ` +
        `the naive baseline—a ${placement.improvement_percentage_points.toFixed(1)} percentage-point gain.`,
      deployment_actions: actions,
      watch_items: [
        "Re-run when heat conditions, resource count, or service radius changes.",
        "Confirm every cell centroid is a feasible and publicly accessible site.",
      ],
      limitations: [
        "This illustrative brief uses synthetic data.",
        "Risk coverage is not an estimate of illnesses or lives saved.",
      ],
      source: "template",
      model: null,
      evidence_fingerprint: "0".repeat(64),
      grounded: true,
    },
  };
}
