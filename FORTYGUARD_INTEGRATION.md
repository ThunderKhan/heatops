# FortyGuard integration

HeatOps implements FortyGuard's asynchronous heatmap flow:

1. `POST /v1/heatmap` with a GeoJSON polygon AOI, time configuration, granularity, and analytic type.
2. Read the returned `activity_id`.
3. Poll `GET /v1/status/{activity_id}` until completion or failure.
4. Validate `result.map_data` as a GeoJSON FeatureCollection.
5. Convert its polygon cells into HeatOps' provider-neutral domain model.

Metric mapping:

| HeatOps metric | FortyGuard `analytic_type` | Unit |
|---|---|---|
| `snapshot` | `tcm` | °C |
| `exceedance` | `exceedance` | hours above threshold |
| `persistence` | `persistence` | longest continuous run in hours |

## Local configuration

Never commit a real key. Copy `.env.example` to `.env`, then set:

```dotenv
HEATOPS_PROVIDER=fortyguard
FORTYGUARD_API_KEY=replace-locally
```

Restart FastAPI after changing `.env`. Run one dashboard analysis. In strict `fortyguard` mode, credential, quota, schema, or timeout failures are surfaced instead of silently switching data. After the first successful live result, `HEATOPS_PROVIDER=auto` provides a clearly labelled mock fallback for demonstrations.

The demonstration AOI is below FortyGuard's documented 10 mi² heatmap limit. No API key is ever sent to the browser.
