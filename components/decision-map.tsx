"use client";

import { useEffect, useRef } from "react";
import type { PlacementResponse, RiskLevel } from "@/lib/types";

const RISK_COLORS: Record<RiskLevel, string> = {
  low: "#c9df8a",
  moderate: "#f2c14e",
  high: "#f47c48",
  critical: "#c93f45",
};

function escapeHtml(value: string) {
  return value.replace(
    /[&<>'"]/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        character
      ] ?? character,
  );
}

export function DecisionMap({ response }: { response: PlacementResponse }) {
  const mapElement = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapElement.current) return;
    let cancelled = false;
    let removeMap: (() => void) | undefined;

    void import("leaflet").then((leafletModule) => {
      if (cancelled || !mapElement.current) return;
      const L = leafletModule.default;
      const map = L.map(mapElement.current, { zoomControl: false, attributionControl: true });
      removeMap = () => map.remove();

      L.control.zoom({ position: "bottomright" }).addTo(map);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);

      const geoJson = L.geoJSON(response.risk_map as never, {
        style: (feature) => {
          const level = (feature?.properties?.risk_level ?? "low") as RiskLevel;
          return {
            color: "#fff8ec",
            weight: 1.2,
            fillColor: RISK_COLORS[level],
            fillOpacity: 0.74,
          };
        },
        onEachFeature: (feature, layer) => {
          const properties = feature.properties;
          layer.bindPopup(`
            <div class="map-popup">
              <strong>${escapeHtml(String(properties.cell_id))}</strong>
              <span class="popup-level">${escapeHtml(String(properties.risk_level))} priority</span>
              <dl>
                <div><dt>Risk score</dt><dd>${Number(properties.risk_score).toFixed(3)}</dd></div>
                <div><dt>Heat hazard</dt><dd>${Number(properties.hazard).toFixed(2)}</dd></div>
                <div><dt>Exposure</dt><dd>${Number(properties.exposure).toFixed(2)}</dd></div>
                <div><dt>Vulnerability</dt><dd>${Number(properties.vulnerability).toFixed(2)}</dd></div>
                <div><dt>Cooling access</dt><dd>${Number(properties.cooling_access).toFixed(2)}</dd></div>
              </dl>
            </div>
          `);
        },
      });

      map.fitBounds(geoJson.getBounds(), { padding: [24, 24] });
      geoJson.addTo(map);

      response.optimized.placements.forEach((placement) => {
        const { latitude, longitude } = placement.site;
        L.circle([latitude, longitude], {
          radius: response.coverage_radius_km * 1000,
          color: "#17373a",
          weight: 1,
          dashArray: "5 6",
          fillColor: "#d8ff68",
          fillOpacity: 0.12,
        }).addTo(map);
        L.circleMarker([latitude, longitude], {
          radius: 9,
          color: "#fffdf5",
          weight: 3,
          fillColor: "#17373a",
          fillOpacity: 1,
        })
          .bindTooltip(`Cooling point ${placement.order}`, { direction: "top" })
          .addTo(map);
      });
    });

    return () => {
      cancelled = true;
      removeMap?.();
    };
  }, [response]);

  return (
    <div ref={mapElement} className="decision-map" aria-label="Interactive heat-risk map" />
  );
}
