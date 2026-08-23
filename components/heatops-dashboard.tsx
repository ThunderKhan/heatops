"use client";

import { useMemo, useState } from "react";
import { DecisionMap } from "@/components/decision-map";
import { ArrowIcon, LayersIcon, PinIcon, ThermometerIcon, TrendIcon } from "@/components/icons";
import { requestPlacementPlan } from "@/lib/api";
import { createDemoResponse } from "@/lib/demo-data";
import type { HeatMetric, PlacementResponse, RiskLevel, Scenario } from "@/lib/types";

const DEFAULT_SCENARIO: Scenario = {
  metric: "snapshot",
  thresholdC: 35,
  resourceCount: 5,
  coverageRadiusKm: 0.75,
};
const LEVELS: RiskLevel[] = ["low", "moderate", "high", "critical"];

export function HeatOpsDashboard() {
  const [scenario, setScenario] = useState(DEFAULT_SCENARIO);
  const [response, setResponse] = useState<PlacementResponse>(() =>
    createDemoResponse(DEFAULT_SCENARIO),
  );
  const [isIllustrative, setIsIllustrative] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const topPlacements = response.optimized.placements.slice(0, 5);
  const highPriorityShare = useMemo(() => {
    const counts = response.risk_map.summary.level_counts;
    return Math.round(
      ((counts.critical + counts.high) / Math.max(1, response.risk_map.summary.cell_count)) * 100,
    );
  }, [response]);

  async function runAnalysis() {
    setIsLoading(true);
    setNotice(null);
    try {
      const result = await requestPlacementPlan(scenario);
      setResponse(result);
      setIsIllustrative(false);
    } catch {
      setResponse(createDemoResponse(scenario));
      setIsIllustrative(true);
      setNotice("The local API is unavailable, so the verified illustrative scenario remains on screen.");
    } finally {
      setIsLoading(false);
    }
  }

  function updateScenario<Key extends keyof Scenario>(key: Key, value: Scenario[Key]) {
    setScenario((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="HeatOps home">
          <span className="brand-mark"><span /></span>
          <span>HeatOps</span>
        </a>
        <div className="topbar-context">
          <span>Urban response workspace</span>
          <span className="context-divider" />
          <span className="live-status"><i /> Decision engine ready</span>
        </div>
        <div className="data-badge">
          <span>{isIllustrative ? "Illustrative" : "API result"}</span>
          <strong>{response.synthetic ? "Synthetic data" : "Verified data"}</strong>
        </div>
      </header>

      <div className="workspace" id="top">
        <aside className="control-panel">
          <div className="control-heading">
            <p className="eyebrow">Scenario 01</p>
            <h1>Plan the next heat response.</h1>
            <p>
              Set operational constraints. HeatOps will maximize modeled risk coverage—not just
              chase the hottest cells.
            </p>
          </div>

          <fieldset className="control-group">
            <legend>Heat intelligence</legend>
            <label>
              Analysis layer
              <select
                value={scenario.metric}
                onChange={(event) => updateScenario("metric", event.target.value as HeatMetric)}
              >
                <option value="snapshot">Temperature snapshot</option>
                <option value="exceedance">Threshold exceedance</option>
                <option value="persistence">Heat persistence</option>
              </select>
            </label>
            <label>
              Alert threshold
              <span className="input-with-unit">
                <input
                  type="number"
                  min="25"
                  max="50"
                  value={scenario.thresholdC}
                  onChange={(event) => updateScenario("thresholdC", Number(event.target.value))}
                />
                <span>°C</span>
              </span>
            </label>
          </fieldset>

          <fieldset className="control-group">
            <legend>Response capacity</legend>
            <label className="range-label">
              <span>Temporary cooling points</span>
              <output>{scenario.resourceCount}</output>
              <input
                type="range"
                min="1"
                max="10"
                value={scenario.resourceCount}
                onChange={(event) => updateScenario("resourceCount", Number(event.target.value))}
              />
            </label>
            <label className="range-label">
              <span>Service radius</span>
              <output>{scenario.coverageRadiusKm.toFixed(2)} km</output>
              <input
                type="range"
                min="0.25"
                max="2"
                step="0.25"
                value={scenario.coverageRadiusKm}
                onChange={(event) =>
                  updateScenario("coverageRadiusKm", Number(event.target.value))
                }
              />
            </label>
          </fieldset>

          <button className="run-button" type="button" onClick={runAnalysis} disabled={isLoading}>
            <span>{isLoading ? "Evaluating scenario…" : "Run placement analysis"}</span>
            <ArrowIcon />
          </button>
          <p className="method-note">
            <span>Method</span> Greedy weighted maximum coverage with baseline guard.
          </p>
        </aside>

        <section className="decision-surface">
          {notice && <div className="notice" role="status">{notice}</div>}
          <div className="surface-header">
            <div>
              <p className="eyebrow">Demo district · 64 analysis cells</p>
              <h2>Cooling resource deployment</h2>
            </div>
            <div className="legend" aria-label="Risk legend">
              {LEVELS.map((level) => (
                <span key={level} className={`legend-${level}`}><i />{level}</span>
              ))}
            </div>
          </div>

          <div className="map-card">
            <DecisionMap response={response} />
            <div className="map-overlay">
              <span>Optimized plan</span>
              <strong>{response.optimized.selected_resource_count} points</strong>
            </div>
            <div className="map-provenance">
              {response.synthetic ? "Synthetic demonstration layer" : "Verified input layers"}
            </div>
          </div>

          <div className="metric-grid">
            <MetricCard
              primary
              icon={<TrendIcon />}
              label="Optimized risk coverage"
              value={response.optimized.covered_risk_percent.toFixed(1)}
              unit="%"
              note={`+${response.improvement_percentage_points.toFixed(1)} pp`}
            />
            <MetricCard
              icon={<LayersIcon />}
              label="Naive baseline"
              value={response.baseline.covered_risk_percent.toFixed(1)}
              unit="%"
              note="top-risk cells"
            />
            <MetricCard
              icon={<PinIcon />}
              label="Cells reached"
              value={String(response.optimized.covered_cell_count)}
              unit={`/${response.risk_map.summary.cell_count}`}
              note="within radius"
            />
            <MetricCard
              icon={<ThermometerIcon />}
              label="High-priority share"
              value={String(highPriorityShare)}
              unit="%"
              note="high + critical"
            />
          </div>

          <div className="details-grid">
            <section className="deployment-table">
              <div className="section-title">
                <div><p className="eyebrow">Recommended deployment</p><h3>Selected cooling points</h3></div>
                <span>{topPlacements.length} shown</span>
              </div>
              <div className="table-head"><span>Priority</span><span>Cell</span><span>Marginal risk</span></div>
              {topPlacements.map((placement) => (
                <div className="table-row" key={placement.site.site_id}>
                  <span className="priority-number">{String(placement.order).padStart(2, "0")}</span>
                  <span>
                    <strong>{placement.site.source_cell_id}</strong>
                    <small>{placement.site.latitude.toFixed(4)}, {placement.site.longitude.toFixed(4)}</small>
                  </span>
                  <span className="risk-value">{placement.marginal_covered_risk.toFixed(3)}</span>
                </div>
              ))}
            </section>

            <aside className="decision-note">
              <p className="eyebrow">Why this plan wins</p>
              <h3>Coverage, not temperature alone.</h3>
              <p>
                The optimized plan separates resources that would otherwise overlap around the
                hottest cells. It reaches <strong>{response.optimized.covered_cell_count - response.baseline.covered_cell_count} additional cells</strong> under the same resource constraint.
              </p>
              <div className="formula">
                <span>Risk formula</span>
                <code>H × (wE·E + wV·V + wA·(1−C))</code>
              </div>
              <p className="caveat">
                Risk coverage is a prioritization proxy. It does not estimate illnesses prevented
                or lives saved.
              </p>
            </aside>
          </div>
        </section>
      </div>
    </main>
  );
}

function MetricCard({
  icon,
  label,
  value,
  unit,
  note,
  primary = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  unit: string;
  note: string;
  primary?: boolean;
}) {
  return (
    <article className={`metric-card${primary ? " metric-primary" : ""}`}>
      <span className="metric-icon">{icon}</span>
      <div><p>{label}</p><strong>{value}<small>{unit}</small></strong></div>
      <em className={primary ? "" : "neutral"}>{note}</em>
    </article>
  );
}
