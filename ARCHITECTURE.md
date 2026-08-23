# HeatOps Architecture

## Design principles

1. The optimization model, not an LLM, makes allocation decisions.
2. External services sit behind interfaces.
3. Raw data, derived scores, and recommendations remain distinguishable.
4. A cached demonstration path is a product requirement.
5. Domain logic stays independent of FastAPI and the React interface.

## Components

### Temperature provider

Returns validated GeoJSON features for one of three metrics:

- snapshot temperature in degrees Celsius;
- exceedance duration in hours;
- persistence duration in hours.

Implementations:

- `MockTemperatureProvider`: current deterministic development provider;
- `FortyGuardTemperatureProvider`: asynchronous submit-and-poll API adapter;
- `CachedTemperatureProvider`: future demo fallback using previously authorized responses.

### Risk engine

Joins heat cells with exposure, vulnerability, and cooling-access layers. It emits both normalized components and a composite prioritization score.

The hazard is a gate: a cell with no heat hazard receives zero heat-priority risk. Exposure, vulnerability, and lack of cooling access form a configurable weighted context score. Individual contributions remain visible in every result.

### Candidate-site service

Loads feasible public intervention locations and rejects sites outside the area or without sufficient metadata.

During Milestone 3, one development-only candidate is generated at each risk-cell centroid. The interface is deliberately separate so these synthetic candidates can later be replaced by feasible public sites from OpenStreetMap or verified municipal data.

### Placement optimizer

Solves budget-constrained maximum coverage. It must expose its assumptions and compare against a simple baseline.

The current solver uses deterministic greedy weighted maximum coverage. At every step it chooses the site covering the largest amount of not-yet-covered risk. It also evaluates a naive highest-risk-cell baseline and will never publish a plan that covers less risk than that baseline.

### API

FastAPI validates requests and exposes domain operations. It contains no optimization or geospatial business rules.

### Web client

The Vinext/React client renders scenario controls, an interactive Leaflet/OpenStreetMap risk layer, optimized resource locations, a naive-baseline comparison, cell explanations, and visible data provenance. It calls FastAPI directly in local development and retains an explicitly labelled deterministic scenario if the API is unavailable.

### Evidence-grounded briefing

The briefing service converts a placement plan into a canonical evidence bundle and SHA-256 fingerprint. Groq may narrate only that bundle into a validated schema. If the key, model, network, or response is unavailable, a deterministic template produces the same schema. Neither narrator can change the optimizer output.

## Initial package structure

```text
src/heatops/
  api.py
  config.py
  domain.py
  providers/
    base.py
    mock.py
  risk/
    context.py
    engine.py
    models.py
  optimization/
    candidates.py
    engine.py
    models.py
tests/
```

## FortyGuard integration boundary

The concrete adapter submits `POST /v1/heatmap`, polls `GET /v1/status/{activity_id}`, validates the completed GeoJSON, and maps it into the internal provider contract. API keys remain server-side. `auto` mode falls back to clearly labelled synthetic heat; `fortyguard` mode fails loudly for integration verification. Authorized response caching remains a later milestone.
