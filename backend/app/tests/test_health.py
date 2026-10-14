"""Health check endpoint unit tests."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health_returns_200():
    """Verify that /api/health returns HTTP 200 with healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "SkillSync AI"
    assert "database" in data


def test_health_alias_returns_200():
    """Verify that /health alias returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_returns_200():
    """Verify that root / returns HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "SkillSync AI" in data["message"]
