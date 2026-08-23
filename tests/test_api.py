from fastapi.testclient import TestClient

from heatops.api import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_heatmap_endpoint_returns_geojson() -> None:
    response = client.post(
        "/api/v1/heatmaps",
        json={
            "bounds": {
                "north": 28.755,
                "south": 28.705,
                "east": -81.315,
                "west": -81.375,
            },
            "metric": "snapshot",
            "threshold_c": 35.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["synthetic"] is True
    assert len(payload["features"]) == 64
    assert payload["features"][0]["geometry"]["type"] == "Polygon"


def test_heatmap_endpoint_rejects_inverted_bounds() -> None:
    response = client.post(
        "/api/v1/heatmaps",
        json={
            "bounds": {"north": 10, "south": 20, "east": 30, "west": 25},
            "metric": "snapshot",
        },
    )

    assert response.status_code == 422


def test_risk_map_endpoint_returns_explainable_geojson() -> None:
    response = client.post(
        "/api/v1/risk-maps",
        json={
            "heatmap": {
                "bounds": {
                    "north": 28.755,
                    "south": 28.705,
                    "east": -81.315,
                    "west": -81.375,
                },
                "metric": "snapshot",
                "threshold_c": 35.0,
            },
            "weights": {
                "exposure": 0.35,
                "vulnerability": 0.40,
                "lack_of_access": 0.25,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["synthetic"] is True
    assert payload["summary"]["cell_count"] == 64
    assert sum(payload["summary"]["level_counts"].values()) == 64
    properties = payload["features"][0]["properties"]
    assert "risk_score" in properties
    assert "exposure_contribution" in properties
    assert "context_source" in properties


def test_risk_map_endpoint_rejects_invalid_weights() -> None:
    response = client.post(
        "/api/v1/risk-maps",
        json={
            "heatmap": {
                "bounds": {"north": 29, "south": 28, "east": -81, "west": -82},
                "metric": "snapshot",
            },
            "weights": {
                "exposure": 0.5,
                "vulnerability": 0.5,
                "lack_of_access": 0.5,
            },
        },
    )

    assert response.status_code == 422
