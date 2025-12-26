import pytest
from fastapi.testclient import TestClient

from aos.api.app import create_app, reset_globals


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Reset global state before and after each test."""
    reset_globals()
    yield
    reset_globals()


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "db_status" in data
        assert "disk_free_mb" in data
        assert "uptime_seconds" in data
