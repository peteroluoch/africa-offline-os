from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from aos.core.config import Settings
from aos.core.health import HealthStatus
from aos.db.engine import connect


# Global database connection
_db_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Get the global database connection."""
    if _db_conn is None:
        raise RuntimeError("Database not initialized")
    return _db_conn


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle with graceful startup and shutdown."""
    global _db_conn
    
    # Startup
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
        return {"status": HealthStatus().status}

    return app
