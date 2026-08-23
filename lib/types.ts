export type HeatMetric = "snapshot" | "exceedance" | "persistence";
export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface Scenario {
  metric: HeatMetric;
  thresholdC: number;
  resourceCount: number;
  coverageRadiusKm: number;
}

export interface RiskProperties {
  cell_id: string;
  heat_metric: HeatMetric;
  heat_value: number;
  heat_unit: "celsius" | "hours";
  heat_threshold_c: number;
  hazard: number;
  exposure: number;
  vulnerability: number;
  cooling_access: number;
  lack_of_access: number;
  exposure_contribution: number;
  vulnerability_contribution: number;
  access_contribution: number;
  risk_score: number;
  risk_level: RiskLevel;
  heat_source: "synthetic" | "fortyguard" | "cache";
  context_source: "synthetic" | "open_data" | "verified";
}

export interface RiskFeature {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: number[][][] };
  properties: RiskProperties;
}

export interface RiskMapResponse {
  type: "FeatureCollection";
  features: RiskFeature[];
  weights: { exposure: number; vulnerability: number; lack_of_access: number };
  summary: {
    cell_count: number;
    mean_score: number;
    maximum_score: number;
    level_counts: Record<RiskLevel, number>;
  };
  synthetic: boolean;
  formula: string;
}

export interface CandidateSite {
  site_id: string;
  source_cell_id: string;
  longitude: number;
  latitude: number;
  source: "cell_centroid" | "openstreetmap" | "verified";
}

export interface SelectedPlacement {
  order: number;
  site: CandidateSite;
  newly_covered_cell_ids: string[];
  marginal_covered_risk: number;
}

export interface PlacementPlan {
  strategy: "optimized" | "highest_risk_baseline";
  requested_resource_count: number;
  selected_resource_count: number;
  placements: SelectedPlacement[];
  covered_cell_ids: string[];
  covered_cell_count: number;
  total_risk_burden: number;
  covered_risk_burden: number;
  covered_risk_percent: number;
}

export interface PlacementResponse {
  risk_map: RiskMapResponse;
  candidate_count: number;
  coverage_radius_km: number;
  optimized: PlacementPlan;
  baseline: PlacementPlan;
  improvement_percentage_points: number;
  synthetic: boolean;
  algorithm: string;
}

export interface ActionBrief {
  headline: string;
  situation_summary: string;
  deployment_actions: string[];
  watch_items: string[];
  limitations: string[];
  source: "template" | "groq";
  model: string | null;
  evidence_fingerprint: string;
  grounded: true;
}

export interface DecisionResponse {
  placement: PlacementResponse;
  brief: ActionBrief;
}
