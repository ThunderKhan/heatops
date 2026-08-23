import type { DecisionResponse, Scenario } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_HEATOPS_API_URL ?? "http://127.0.0.1:8000";

export async function requestDecision(
  scenario: Scenario,
  signal?: AbortSignal,
): Promise<DecisionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/decisions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify({
      risk_map: {
        heatmap: {
          bounds: {
            north: 28.755,
            south: 28.705,
            east: -81.315,
            west: -81.375,
          },
          metric: scenario.metric,
          threshold_c: scenario.thresholdC,
        },
      },
      resource_count: scenario.resourceCount,
      coverage_radius_km: scenario.coverageRadiusKm,
      prefer_ai_brief: true,
    }),
  });

  if (!response.ok) throw new Error(`HeatOps API returned ${response.status}`);
  return response.json() as Promise<DecisionResponse>;
}
