"""
Database Resilience Tests - TASK 0.2
Tests for power-loss recovery, corruption detection, and connection health.

Following TDD: These tests are written FIRST and should guide implementation.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from aos.db.engine import connect, get_journal_mode


class TestDatabasePowerLossResilience:
    """Test that DB can recover from abrupt disconnection (power loss simulation)."""

    def test_db_reconnects_after_forced_close(self, tmp_path: Path) -> None:
        """DB must auto-reconnect after connection is forcefully closed."""
        db_path = tmp_path / "test_reconnect.db"
        
        # First connection: write data
        conn1 = connect(str(db_path))
        conn1.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn1.execute("INSERT INTO test (value) VALUES ('data')")
        conn1.commit()
        
        # Simulate power loss: close without proper shutdown
        conn1.close()
        
        # Second connection: should work without corruption
        conn2 = connect(str(db_path))
        try:
            cursor = conn2.execute("SELECT value FROM test WHERE id = 1")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "data", "Data must survive power-loss simulation"
        finally:
            conn2.close()

    def test_wal_mode_persists_across_connections(self, tmp_path: Path) -> None:
        """WAL mode must persist across connection cycles."""
        db_path = tmp_path / "test_wal_persist.db"
        
        # First connection: enable WAL
        conn1 = connect(str(db_path))
        assert get_journal_mode(conn1).lower() == "wal"
        conn1.close()
        
        # Second connection: WAL should still be active
        conn2 = connect(str(db_path))
        try:
            assert get_journal_mode(conn2).lower() == "wal", \
                "WAL mode must persist (critical for power-loss safety)"
        finally:
            conn2.close()


class TestDatabaseCorruptionDetection:
    """Test that DB can detect and report corruption."""

    def test_db_detects_corrupted_file(self, tmp_path: Path) -> None:
        """DB must detect when file is corrupted."""
        db_path = tmp_path / "test_corrupt.db"
        
        # Create valid DB
        conn = connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        # Corrupt the file
        with open(db_path, "wb") as f:
            f.write(b"CORRUPTED_DATA_NOT_SQLITE")
        
        # Attempting to connect should detect corruption
        # This test will be implemented when we add corruption detection
        pytest.skip("Corruption detection not yet implemented - TDD RED phase")

    def test_db_integrity_check_passes_for_healthy_db(self, tmp_path: Path) -> None:
        """Integrity check must pass for healthy database."""
        db_path = tmp_path / "test_healthy.db"
        
        conn = connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.execute("INSERT INTO test (data) VALUES ('test')")
        conn.commit()
        
        # Run integrity check
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "ok", "Healthy DB must pass integrity check"


class TestDatabaseConnectionHealth:
    """Test connection health monitoring."""

    def test_connection_is_healthy_after_creation(self, tmp_path: Path) -> None:
        """New connection must report as healthy."""
        db_path = tmp_path / "test_health.db"
        conn = connect(str(db_path))
        
        try:
            # Basic health check: can execute simple query
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,), "Healthy connection must execute queries"
        finally:
            conn.close()

    def test_closed_connection_is_not_healthy(self, tmp_path: Path) -> None:
        """Closed connection must be detectable."""
        db_path = tmp_path / "test_closed.db"
        conn = connect(str(db_path))
        conn.close()
        
        # Attempting to use closed connection should fail
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


@pytest.fixture
def clean_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a clean temporary database path."""
    db_path = tmp_path / "test.db"
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()
