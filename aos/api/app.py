from __future__ import annotations

import sqlite3
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from aos.core.config import Settings
from aos.core.health import HealthStatus, check_db_health, get_disk_space, get_uptime
from aos.db.engine import connect


# Global database connection
_db_conn: sqlite3.Connection | None = None
# Boot timestamp for uptime tracking
_boot_time: float | None = None


def get_db() -> sqlite3.Connection:
    """Get the global database connection."""
    if _db_conn is None:
        raise RuntimeError("Database not initialized")
    return _db_conn


def reset_globals() -> None:
    """Reset global state for testing purposes."""
    global _db_conn, _boot_time
    if _db_conn:
        _db_conn.close()
    _db_conn = None
    _boot_time = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle with graceful startup and shutdown."""
    global _db_conn, _boot_time
    
    # Startup
    _boot_time = time.time()
    settings = Settings()
    _db_conn = connect(settings.sqlite_path)
    print(f"[A-OS] Started - DB: {settings.sqlite_path} (WAL mode)")
    
    try:
        yield
    finally:
        # Shutdown
        if _db_conn:
            _db_conn.close()
            print("[A-OS] Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="A-OS",
        version="0.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict:
        """
        Comprehensive health check for production monitoring.
        
        Returns:
            Health status including disk space, uptime, and DB status
        """
        # Gather health metrics
        disk_free = get_disk_space()
        uptime = get_uptime(_boot_time)
        db_status = check_db_health(_db_conn)
        
        # Create comprehensive health response
        status = HealthStatus(
            status="ok",
            disk_free_mb=disk_free,
            uptime_seconds=uptime,
            db_status=db_status,
        )
        
        return {
            "status": status.status,
            "disk_free_mb": status.disk_free_mb,
            "uptime_seconds": status.uptime_seconds,
            "db_status": status.db_status,
        }

    return app
