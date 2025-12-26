"""
Mesh Queue - Persistent store-and-forward for mesh events.
Ensures zero data loss during network partitions.
"""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any


class MeshQueue:
    """
    Persistent SQLite-backed queue for outbound mesh events.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create the mesh_queue table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mesh_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_node_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    last_attempt REAL,
                    priority INTEGER DEFAULT 1,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mesh_target ON mesh_queue(target_node_id)")

    def enqueue(self, target_node_id: str, event_type: str, payload: dict[str, Any], priority: int = 1) -> int:
        """Add an event to the outbound queue."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO mesh_queue (target_node_id, event_type, payload, priority, created_at) VALUES (?, ?, ?, ?, ?)",
                (target_node_id, event_type, json.dumps(payload), priority, time.time())
            )
            return cursor.lastrowid

    def get_pending(self, target_node_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get pending events for synchronization."""
        query = "SELECT id, target_node_id, event_type, payload, attempts, priority FROM mesh_queue"
        params = []

        if target_node_id:
            query += " WHERE target_node_id = ?"
            params.append(target_node_id)

        query += " ORDER BY priority DESC, created_at ASC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def mark_success(self, event_id: int) -> None:
        """Remove a successfully delivered event from the queue."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM mesh_queue WHERE id = ?", (event_id,))

    def mark_failed(self, event_id: int) -> None:
        """Increment attempt count and update last attempt time."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE mesh_queue SET attempts = attempts + 1, last_attempt = ? WHERE id = ?",
                (time.time(), event_id)
            )

    def prune_old_events(self, max_age_days: int = 7) -> int:
        """Remove events that have exceeded the retention period."""
        cutoff = time.time() - (max_age_days * 86400)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM mesh_queue WHERE created_at < ?", (cutoff,))
            return cursor.rowcount
