import sqlite3

import pytest
from fastapi.testclient import TestClient

from aos.api.app import create_app, reset_globals
from aos.core.config import Settings


@pytest.fixture(autouse=True)
def cleanup():
    reset_globals()
    yield
    reset_globals()

def test_app_startup_migrates_db(tmp_path, monkeypatch):
    """Verify that starting the app applies migrations and creates tables."""
    db_path = tmp_path / "app_test.db"

    # Mock settings to use temp DB
    monkeypatch.setattr("aos.api.app.Settings", lambda: Settings(sqlite_path=str(db_path)))

    app = create_app()

    # Using TestClient as context manager triggers lifespan events
    with TestClient(app) as client:
        # Check if tables exist in the DB
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "schema_migrations" in tables
        assert "nodes" in tables
        assert "operators" in tables
        assert "node_config" in tables

        # Verify health endpoint reports DB as healthy
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["db_status"] == "healthy"

        conn.close()
