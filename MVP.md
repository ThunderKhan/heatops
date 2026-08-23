# HeatOps MVP

## Scope

The MVP optimizes the placement of one generic temporary cooling resource, representing a staffed water point or temporary cooling point, inside one supported demonstration area.

## Required capabilities

- [x] Run locally without a FortyGuard API key.
- [x] Return deterministic synthetic heat data as GeoJSON.
- [x] Preserve snapshot, exceedance, and persistence units.
- [ ] Fetch and cache a real FortyGuard heatmap.
- [ ] Display the heat layer on an interactive map.
- [ ] Calculate an inspectable heat-risk score.
- [ ] load candidate intervention locations.
- [ ] Select up to `k` locations with a maximum-coverage optimizer.
- [ ] Compare optimized placement with a naive baseline.
- [ ] Explain selected locations.
- [ ] Export a short heat-action brief.
- [ ] Complete a deployed end-to-end demonstration.

## MVP risk model

For grid cell `i`:

\[
R_i = H_i \times E_i \times V_i \times (1-C_i)
\]

Where:

- `H`: normalized heat hazard;
- `E`: normalized exposure;
- `V`: normalized vulnerability;
- `C`: normalized existing cooling access.

Every component must remain separately visible. The composite score is a prioritization proxy, not a prediction of illness or mortality.

## Done means

A judge can select an event scenario, compare the unoptimized and optimized plans, change the number of available resources, and see a reproducible change in estimated vulnerable heat exposure coverage.

