from __future__ import annotations

import sqlite3
from aos.api.state import core_state

def get_db() -> sqlite3.Connection:
    """Get the global database connection from core state."""
    db = core_state.db_conn
    if db is None:
        raise RuntimeError("Database not initialized")
    return db
