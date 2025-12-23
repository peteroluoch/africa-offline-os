"""
Entrypoint & Integration Tests - TASK 0.4
Tests for graceful boot, corruption recovery, and system initialization.

Following TDD: These tests validate the complete system startup flow.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aos.api.app import create_app, reset_globals
from aos.db.engine import connect


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Reset global state before and after each test."""
    reset_globals()
    yield
    reset_globals()


class TestGracefulBoot:
    """Test that application boots gracefully under various conditions."""

    def test_app_boots_with_clean_database(self, tmp_path: Path) -> None:
        """App must boot successfully with a clean database."""
        import os
        db_path = str(tmp_path / "clean.db")
        os.environ["AOS_SQLITE_PATH"] = db_path
        
        try:
            app = create_app()
            with TestClient(app) as client:
                # Verify app is responsive
                resp = client.get("/health")
                assert resp.status_code == 200
                
                data = resp.json()
                assert data["status"] == "ok"
                assert data["db_status"] == "healthy"
        finally:
            if "AOS_SQLITE_PATH" in os.environ:
                del os.environ["AOS_SQLITE_PATH"]

    def test_app_boots_with_existing_database(self, tmp_path: Path) -> None:
        """App must boot successfully with an existing database."""
        db_path = tmp_path / "existing.db"
        
        # Pre-create database with data
        conn = connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.execute("INSERT INTO test (data) VALUES ('existing')")
        conn.commit()
        conn.close()
        
        # Boot app with existing DB
        import os
        os.environ["AOS_SQLITE_PATH"] = str(db_path)
        
        try:
            app = create_app()
            with TestClient(app) as client:
                resp = client.get("/health")
                assert resp.status_code == 200
                assert resp.json()["db_status"] == "healthy"
        finally:
            if "AOS_SQLITE_PATH" in os.environ:
                del os.environ["AOS_SQLITE_PATH"]


class TestCorruptionRecovery:
    """Test that app handles database corruption gracefully."""

    def test_app_detects_corrupted_database(self, tmp_path: Path) -> None:
        """App must detect when database is corrupted."""
        db_path = tmp_path / "corrupted.db"
        
        # Create corrupted file
        with open(db_path, "wb") as f:
            f.write(b"NOT_A_VALID_SQLITE_DATABASE")
        
        import os
        os.environ["AOS_SQLITE_PATH"] = str(db_path)
        
        try:
            # App should handle corruption gracefully
            # This test will be enhanced when we add corruption handling
            pytest.skip("Corruption recovery not yet implemented - TDD RED phase")
        finally:
            if "AOS_SQLITE_PATH" in os.environ:
                del os.environ["AOS_SQLITE_PATH"]


class TestFirstBootInitialization:
    """Test that app initializes properly on first boot."""

    def test_app_creates_database_on_first_boot(self, tmp_path: Path) -> None:
        """App must create database if it doesn't exist."""
        db_path = tmp_path / "new.db"
        if db_path.exists():
            db_path.unlink()
        assert not db_path.exists(), "DB should not exist before first boot"
        
        import os
        os.environ["AOS_SQLITE_PATH"] = str(db_path)
        
        try:
            app = create_app()
            with TestClient(app) as client:
                # Trigger lifespan startup
                resp = client.get("/health")
                assert resp.status_code == 200
                
                # Verify DB was created
                assert db_path.exists(), "DB must be created on first boot"
                
                # Verify WAL mode is enabled
                conn = sqlite3.connect(str(db_path))
                cursor = conn.execute("PRAGMA journal_mode")
                mode = cursor.fetchone()
                conn.close()
                
                assert mode[0].lower() == "wal", "WAL mode must be enabled on first boot"
        finally:
            if "AOS_SQLITE_PATH" in os.environ:
                del os.environ["AOS_SQLITE_PATH"]


class TestSystemIntegration:
    """Test complete system integration."""

    def test_health_endpoint_integration(self) -> None:
        """Health endpoint must integrate all monitoring components."""
        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            
            data = resp.json()
            
            # Verify all health components are present
            assert "status" in data
            assert "disk_free_mb" in data
            assert "uptime_seconds" in data
            assert "db_status" in data
            
            # Verify data types
            assert isinstance(data["disk_free_mb"], (int, float))
            assert isinstance(data["uptime_seconds"], (int, float))
            assert data["db_status"] in ["healthy", "degraded", "unavailable"]

    def test_system_survives_multiple_requests(self) -> None:
        """System must remain stable under multiple requests."""
        app = create_app()
        with TestClient(app) as client:
            # Make multiple requests
            for _ in range(10):
                resp = client.get("/health")
                assert resp.status_code == 200
                assert resp.json()["status"] == "ok"
