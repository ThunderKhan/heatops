# HeatOps

HeatOps is an explainable decision-support system for placing temporary cooling and drinking-water resources during urban heat events.

Instead of stopping at **where is it hot?**, HeatOps is designed to answer:

> Given a limited response budget, where should temporary resources be placed to cover the greatest vulnerable heat exposure?

HeatOps is being built for the FortyGuard Hackathon'26 across the Government & Environment, Resilient Cities & Infrastructure, Agentic AI, and Data Analysis & Correlation tracks.

## Current milestone

Milestone 5 connects live temperature intelligence and turns optimizer evidence into an operational brief:

- a FortyGuard submit-and-poll provider for real GeoJSON heatmaps;
- explicit live, synthetic, and mixed-provenance states;
- a canonical evidence bundle and fingerprint for every recommendation;
- optional Groq narration constrained to verified optimizer facts;
- a deterministic briefing fallback requiring no LLM key;
- downloadable Markdown action briefs and end-to-end decision tests.

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

No key is required for the deterministic demo. To use your FortyGuard key, place it only in `.env` and set `HEATOPS_PROVIDER=fortyguard`. Use `auto` after verification if you want a synthetic fallback when the remote service is unavailable.

A Groq key is optional. When `GROQ_API_KEY` is present, HeatOps uses `qwen/qwen3.6-27b` to narrate the verified evidence bundle. Without it—or if Groq fails—the action brief is generated deterministically. The optimizer, not the LLM, always selects locations.

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
[FORTYGUARD_INTEGRATION.md](FORTYGUARD_INTEGRATION.md), [AI_BRIEFING.md](AI_BRIEFING.md),
[RISK_MODEL.md](RISK_MODEL.md), [OPTIMIZATION_MODEL.md](OPTIMIZATION_MODEL.md), and
[MILESTONE_5_COMMITS.md](MILESTONE_5_COMMITS.md).
