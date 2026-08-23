# HeatOps

HeatOps is an explainable decision-support system for placing temporary cooling and drinking-water resources during urban heat events.

Instead of stopping at **where is it hot?**, HeatOps is designed to answer:

> Given a limited response budget, where should temporary resources be placed to cover the greatest vulnerable heat exposure?

HeatOps is being built for the FortyGuard Hackathon'26 across the Government & Environment, Resilient Cities & Infrastructure, Agentic AI, and Data Analysis & Correlation tracks.

## Current milestone

Milestone 4 turns the resource-placement engine into a judge-ready decision dashboard:

- a working first screen with an explicitly labelled synthetic scenario;
- React/Vinext scenario controls connected to the FastAPI placement endpoint;
- an interactive Leaflet/OpenStreetMap risk layer with inspectable cell scores;
- optimized cooling points, service radii, and a naive-baseline comparison;
- a responsive operations-workspace design with loading and fallback states;
- browser CORS configuration, frontend rendering tests, and existing domain tests.

The mock provider is deliberate. It allows the risk model, optimizer, map, and tests to be developed before hackathon API credentials arrive. It will later be replaced by a FortyGuard adapter without changing the rest of the application.

## Quick start on Windows PowerShell

```powershell
git clone https://github.com/ThunderKhan/heatops.git
cd heatops

py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

Copy-Item .env.example .env
pytest
python -m uvicorn heatops.api:app --reload
```

In a second PowerShell terminal:

```powershell
cd heatops
npm install
npm run dev
```

Open `http://localhost:5173` for the dashboard and `http://127.0.0.1:8000/docs`
for the API. Execute `POST /api/v1/heatmaps` for the
temperature layer, `POST /api/v1/risk-maps` for the enriched risk layer, or
`POST /api/v1/placement-plans` for an optimized intervention plan.

Example body:

```json
{
  "bounds": {
    "north": 28.755,
    "south": 28.705,
    "east": -81.315,
    "west": -81.375
  },
  "metric": "snapshot",
  "threshold_c": 35.0
}
```

No real API key is required. If FastAPI is not running, the dashboard remains usable with an explicitly labelled illustrative scenario; changing resource count or service radius still produces deterministic demo changes.

## Scientific integrity

- `snapshot` values represent degrees Celsius at one time.
- `exceedance` values represent the number of hours above a threshold.
- `persistence` values represent the longest continuous run of hours above a threshold.
- Mock values are synthetic and are never presented as observations.
- Future public-health outputs will be described as decision support, not clinical advice.
- Uncertainty and missing-data limitations will remain visible in the product.

## Repository direction

```text
FortyGuard or mock provider
        -> heat-risk model
        -> candidate resource sites
        -> placement optimizer
        -> interactive map and action brief
```

See [MVP.md](MVP.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DASHBOARD.md](DASHBOARD.md),
[RISK_MODEL.md](RISK_MODEL.md), [OPTIMIZATION_MODEL.md](OPTIMIZATION_MODEL.md), and
[MILESTONE_4_COMMITS.md](MILESTONE_4_COMMITS.md).
