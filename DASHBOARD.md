# HeatOps dashboard

## Decision story

The dashboard is designed to let a judge understand the product in one screen: choose operational constraints, see where risk is concentrated, compare optimized placement with a naive baseline, and inspect why a cell was prioritized.

## Interaction model

1. Choose a heat layer and alert threshold.
2. Set the available number of temporary cooling points and their service radius.
3. Run placement analysis.
4. Inspect selected points, coverage circles, cell-level risk components, and percentage-point improvement over the baseline.

When `NEXT_PUBLIC_HEATOPS_API_URL` is reachable, the dashboard displays a live API result. Otherwise it keeps an explicitly labelled, deterministic synthetic scenario on screen. This fallback is for product demonstration only and never claims to be observed data.

## Visual and scientific conventions

- Low-to-critical risk colors encode the composite prioritization score.
- Point circles show modeled service radius, not walking-time accessibility.
- Coverage is a fraction of modeled risk burden reached under the stated radius.
- The comparison baseline places resources on the highest-risk cells without accounting for overlapping coverage.
- Map popups expose hazard, exposure, vulnerability, and cooling access.
- The interface states that coverage is not an estimate of illness or mortality prevented.

## Local configuration

Copy `.env.example` to `.env`. The default dashboard URL is `http://localhost:5173`, and the default API URL is `http://127.0.0.1:8000`. Adjust `HEATOPS_CORS_ORIGINS` if the frontend runs on another trusted local origin.
