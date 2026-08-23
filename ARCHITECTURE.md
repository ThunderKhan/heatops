# HeatOps Architecture

## Design principles

1. The optimization model, not an LLM, makes allocation decisions.
2. External services sit behind interfaces.
3. Raw data, derived scores, and recommendations remain distinguishable.
4. A cached demonstration path is a product requirement.
5. Domain logic stays independent of FastAPI and the eventual React interface.

## Components

### Temperature provider

Returns validated GeoJSON features for one of three metrics:

- snapshot temperature in degrees Celsius;
- exceedance duration in hours;
- persistence duration in hours.

Implementations:

- `MockTemperatureProvider`: current deterministic development provider;
- `FortyGuardTemperatureProvider`: future asynchronous API adapter;
- `CachedTemperatureProvider`: future demo fallback using previously authorized responses.

### Risk engine

Joins heat cells with exposure, vulnerability, and cooling-access layers. It emits both normalized components and a composite prioritization score.

The hazard is a gate: a cell with no heat hazard receives zero heat-priority risk. Exposure, vulnerability, and lack of cooling access form a configurable weighted context score. Individual contributions remain visible in every result.

### Candidate-site service

Loads feasible public intervention locations and rejects sites outside the area or without sufficient metadata.

### Placement optimizer

Solves budget-constrained maximum coverage. It must expose its assumptions and compare against a simple baseline.

### API

FastAPI validates requests and exposes domain operations. It contains no optimization or geospatial business rules.

### Web client

The future React client will render layers, scenario controls, comparisons, explanations, and provenance.

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
tests/
```

## FortyGuard integration boundary

The concrete adapter will be implemented only after the hackathon credentials and current request schema are available. It will handle submit-and-poll task behavior, timeouts, validation, caching, and sanitized errors without leaking the API key.
