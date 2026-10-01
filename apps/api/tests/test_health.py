"""Tests for Health, Liveness, and Readiness endpoints (API Contract v2 §84)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_probe_returns_200():
    """Verify /health/live returns HTTP 200 with live status and correlation header."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers


def test_readiness_probe_returns_200():
    """Verify /health/ready returns HTTP 200 and checks object."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["configuration"] == "ok"
    assert "X-Request-ID" in response.headers


def test_api_v1_health_returns_metadata():
    """Verify /api/v1/health returns service metadata and version."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "MindBridge" in data["service"]


def test_preserves_inbound_request_id():
    """Verify client-supplied X-Request-ID is preserved across processing."""
    custom_id = "test-req-uuid-12345"
    response = client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
