# HeatOps

HeatOps is an explainable decision-support system for placing temporary cooling and drinking-water resources during urban heat events.

Instead of stopping at **where is it hot?**, HeatOps is designed to answer:

> Given a limited response budget, where should temporary resources be placed to cover the greatest vulnerable heat exposure?

HeatOps is being built for the FortyGuard Hackathon'26 across the Government & Environment, Resilient Cities & Infrastructure, Agentic AI, and Data Analysis & Correlation tracks.

## Current milestone

Milestone 2 adds an explainable risk engine to the Milestone 1 temperature pipeline:

- deterministic synthetic exposure, vulnerability, and cooling-access layers;
- metric-aware heat-hazard normalization;
- configurable, validated risk weights;
- per-component contribution values;
- low, moderate, high, and critical classifications;
- a risk-enriched GeoJSON endpoint and summary;
- mathematical invariant and API tests.

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
uvicorn heatops.api:app --reload
```

Open `http://127.0.0.1:8000/docs`. Execute `POST /api/v1/heatmaps` for the
temperature layer or `POST /api/v1/risk-maps` for the enriched risk layer.

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

No real API key is required for this milestone.

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

See [MVP.md](MVP.md), [ARCHITECTURE.md](ARCHITECTURE.md),
[RISK_MODEL.md](RISK_MODEL.md), and [MILESTONE_2_COMMITS.md](MILESTONE_2_COMMITS.md).
