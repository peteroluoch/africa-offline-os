"""
Sync Engine
Core synchronization engine for peer-to-peer data sync with conflict resolution.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from aos.core.sync.protocol import SyncChange
from aos.core.sync.vector_clock import (
    Conflict,
    ConflictResolutionStrategy,
    LastWriteWins,
    VectorClock,
)

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher

logger = logging.getLogger(__name__)

class SyncEngine:
    """
    Core synchronization engine.
    Handles delta computation, conflict detection, and change application.
    """

    def __init__(
        self,
        node_id: str,
        db_conn: sqlite3.Connection,
        event_bus: EventDispatcher | None = None,
        conflict_strategy: ConflictResolutionStrategy | None = None
    ):
        self.node_id = node_id
        self.db = db_conn
        self.event_bus = event_bus
        self.conflict_strategy = conflict_strategy or LastWriteWins()
        self.vector_clock = VectorClock()
        self._init_sync_tables()

    def _init_sync_tables(self):
        """Initialize sync state tables."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                peer_id TEXT PRIMARY KEY,
                last_sync_timestamp INTEGER NOT NULL,
                vector_clock TEXT NOT NULL,
                sync_status TEXT NOT NULL,
                last_error TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sync_conflicts (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                local_value TEXT NOT NULL,
                remote_value TEXT NOT NULL,
                local_clock TEXT NOT NULL,
                remote_clock TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                resolved INTEGER DEFAULT 0,
                resolution TEXT
            )
        """)

        self.db.commit()

    def compute_delta(self, peer_id: str, since_timestamp: int) -> list[SyncChange]:
        """
        Compute changes since last sync with peer.
        Returns list of changes to send.
        """
        changes = []

        # Get changes from each syncable table
        for table in ['farmers', 'harvests', 'vehicles', 'routes']:
            cursor = self.db.execute(
                f"SELECT * FROM {table} WHERE updated_at > ?",
                (since_timestamp,)
            )

            for row in cursor.fetchall():
                # Convert row to dict
                columns = [desc[0] for desc in cursor.description]
                data = dict(zip(columns, row, strict=False))

                # Increment our vector clock
                self.vector_clock.increment(self.node_id)

                change = SyncChange(
                    entity_type=table[:-1],  # Remove 's' (farmers -> farmer)
                    entity_id=data.get('id', ''),
                    operation='update',  # Simplified - could track creates/deletes
                    data=data,
                    vector_clock=self.vector_clock.copy(),
                    timestamp=data.get('updated_at', 0),
                    node_id=self.node_id
                )
                changes.append(change)

        logger.info(f"Computed {len(changes)} changes for peer {peer_id}")
        return changes

    def apply_changes(self, changes: list[SyncChange], peer_id: str) -> tuple[int, int]:
        """
        Apply incoming changes from peer.
        Returns: (applied_count, conflict_count)
        """
        applied = 0
        conflicts = 0

        for change in changes:
            try:
                # Update our vector clock
                self.vector_clock.update(change.vector_clock)

                # Check for conflicts
                if self._has_conflict(change):
                    conflicts += 1
                    self._handle_conflict(change, peer_id)
                else:
                    self._apply_change(change)
                    applied += 1

            except Exception as e:
                logger.error(f"Error applying change {change.entity_id}: {e}")

        # Update sync state
        self._update_sync_state(peer_id)

        logger.info(f"Applied {applied} changes, {conflicts} conflicts from peer {peer_id}")
        return applied, conflicts

    def _has_conflict(self, change: SyncChange) -> bool:
        """Check if incoming change conflicts with local data."""
        table = change.entity_type + 's'  # farmer -> farmers

        cursor = self.db.execute(
            f"SELECT updated_at FROM {table} WHERE id = ?",
            (change.entity_id,)
        )
        row = cursor.fetchone()

        if not row:
            return False  # No local version = no conflict

        local_timestamp = row[0]

        # Conflict if local was updated after the incoming change
        return local_timestamp > change.timestamp

    def _apply_change(self, change: SyncChange):
        """Apply a non-conflicting change to local database."""
        table = change.entity_type + 's'
        data = change.data

        # Build INSERT OR REPLACE query
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])

        self.db.execute(
            f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(data.values())
        )
        self.db.commit()

    def _handle_conflict(self, change: SyncChange, peer_id: str):
        """Handle a conflicting change using resolution strategy."""
        table = change.entity_type + 's'

        # Get local version
        cursor = self.db.execute(
            f"SELECT * FROM {table} WHERE id = ?",
            (change.entity_id,)
        )
        row = cursor.fetchone()

        if not row:
            # No local version - just apply
            self._apply_change(change)
            return

        # Convert to dict
        columns = [desc[0] for desc in cursor.description]
        local_data = dict(zip(columns, row, strict=False))

        # Create conflict objects
        local_clock = self.vector_clock.copy()
        remote_clock = change.vector_clock

        # Try to resolve
        resolution = self.conflict_strategy.resolve(
            local_data, change.data, local_clock, remote_clock
        )

        if resolution is None:
            # Manual resolution required
            self._store_conflict(change, local_data, local_clock, remote_clock)
        else:
            # Apply resolved value
            change.data = resolution
            self._apply_change(change)

    def _store_conflict(self, change: SyncChange, local_data: dict, local_clock: VectorClock, remote_clock: VectorClock):
        """Store unresolved conflict for manual review."""
        import json

        conflict_id = f"{change.entity_type}_{change.entity_id}_{int(datetime.now(UTC).timestamp())}"

        self.db.execute("""
            INSERT INTO sync_conflicts 
            (id, entity_type, entity_id, local_value, remote_value, local_clock, remote_clock, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conflict_id,
            change.entity_type,
            change.entity_id,
            json.dumps(local_data),
            json.dumps(change.data),
            local_clock.to_json(),
            remote_clock.to_json(),
            int(datetime.now(UTC).timestamp())
        ))
        self.db.commit()

        logger.warning(f"Stored conflict {conflict_id} for manual resolution")

    def _update_sync_state(self, peer_id: str):
        """Update sync state after successful sync."""
        now = int(datetime.now(UTC).timestamp())

        self.db.execute("""
            INSERT OR REPLACE INTO sync_state 
            (peer_id, last_sync_timestamp, vector_clock, sync_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            peer_id,
            now,
            self.vector_clock.to_json(),
            'synced',
            now,
            now
        ))
        self.db.commit()

    def get_sync_state(self, peer_id: str) -> dict | None:
        """Get sync state for a peer."""
        cursor = self.db.execute(
            "SELECT * FROM sync_state WHERE peer_id = ?",
            (peer_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row, strict=False))

    def get_conflicts(self) -> list[Conflict]:
        """Get all unresolved conflicts."""
        import json

        cursor = self.db.execute(
            "SELECT * FROM sync_conflicts WHERE resolved = 0"
        )

        conflicts = []
        for row in cursor.fetchall():
            conflict = Conflict(
                id=row[0],
                entity_type=row[1],
                entity_id=row[2],
                local_value=json.loads(row[3]),
                remote_value=json.loads(row[4]),
                local_clock=VectorClock.from_json(row[5]),
                remote_clock=VectorClock.from_json(row[6]),
                created_at=row[7],
                resolved=bool(row[8]),
                resolution=json.loads(row[9]) if row[9] else None
            )
            conflicts.append(conflict)

        return conflicts
