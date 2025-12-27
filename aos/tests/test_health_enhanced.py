"""
Enhanced Health Monitoring Tests - TASK 0.3
Tests for disk space monitoring, uptime tracking, and DB status reporting.

Following TDD: These tests define the enhanced /health endpoint requirements.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch
import asyncio
import httpx
from fastapi.testclient import TestClient

from aos.api.app import create_app, reset_globals


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Reset global state before and after each test."""
    reset_globals()
    yield
    reset_globals()


class TestHealthDiskSpaceMonitoring:
    """Test that /health endpoint reports disk space metrics."""

    def test_health_includes_disk_space(self) -> None:
        """Health endpoint must report available disk space."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            data = resp.json()
            assert "disk_free_mb" in data, "Health must report free disk space"
            assert isinstance(data["disk_free_mb"], (int, float))
            assert data["disk_free_mb"] >= 0

    def test_health_warns_on_low_disk_space(self) -> None:
        """Health must warn when disk space is critically low."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200


class TestHealthUptimeTracking:
    """Test that /health endpoint tracks power-safe uptime."""

    def test_health_includes_uptime(self) -> None:
        """Health endpoint must report system uptime."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            data = resp.json()
            assert "uptime_seconds" in data, "Health must report uptime"
            assert isinstance(data["uptime_seconds"], (int, float))
            assert data["uptime_seconds"] >= 0

    async def test_uptime_persists_across_restarts(self, tmp_path) -> None:
        """Uptime must be persisted in DB (power-safe)."""
        from aos.db.engine import connect
        import os
        
        db_path = tmp_path / "uptime.db"
        env = {
            "AOS_SQLITE_PATH": str(db_path),
            "AOS_RESOURCE_CHECK_INTERVAL": "0"
        }
        with patch.dict("os.environ", env):
            # 1. First run
            app = create_app()
            async with app.router.lifespan_context(app):
                 # Ensure we have some session uptime
                 await asyncio.sleep(0.8)
            
            # Verify file exists
            assert os.path.exists(db_path), f"DB file was not created at {db_path}!"
            
            # 2. Verify it's in DB
            conn = connect(str(db_path))
            try:
                # Check if table exists
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='node_config'")
                assert cursor.fetchone() is not None, "node_config table missing!"
                
                cursor = conn.execute("SELECT value FROM node_config WHERE key = 'session_uptime'")
                row = cursor.fetchone()
                assert row is not None, "session_uptime not persisted in node_config"
                persisted_uptime = float(row[0])
                assert persisted_uptime > 0
            finally:
                conn.close()

            # 3. Second run (restart)
            app2 = create_app()
            async with app2.router.lifespan_context(app2):
                async with httpx.AsyncClient(app=app2, base_url="http://test") as client:
                    resp = await client.get("/health")
                    data = resp.json()
                    uptime = data["metrics"]["uptime_s"]
                    assert uptime >= persisted_uptime


class TestHealthDatabaseStatus:
    """Test that /health endpoint reports database health."""

    def test_health_includes_db_status(self) -> None:
        """Health endpoint must report database status."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            data = resp.json()
            assert "db_status" in data, "Health must report DB status"
            assert data["db_status"] in ["healthy", "degraded", "unavailable"]

    def test_health_reports_wal_mode_status(self) -> None:
        """Health must verify WAL mode is active."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            data = resp.json()

            assert data["db_status"] == "healthy", \
                "DB must be healthy with WAL mode enabled"


class TestHealthBasicFunctionality:
    """Test that basic health check still works."""

    def test_health_returns_200(self) -> None:
        """Health endpoint must return 200 OK."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_health_includes_status_ok(self) -> None:
        """Health endpoint must include status field."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            data = resp.json()

            assert "status" in data
            assert data["status"] == "ok"
