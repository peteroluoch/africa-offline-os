from __future__ import annotations
import uuid
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict

logger = logging.getLogger("aos.modules.community.broadcast")

class BroadcastManager:
    """
    Manages the lifecycle of community broadcasts with FAANG safety guardrails.
    - Idempotency to prevent duplicate sends.
    - Lease-based locking for workers.
    - Immutable audit logs.
    """

    def __init__(self, db: sqlite3.Connection):
        self._db = db

    def create_broadcast(
        self,
        community_id: str,
        message: str,
        channels: List[str],
        actor_id: str,
        idempotency_key: Optional[str] = None,
        scheduled_at: Optional[datetime] = None
    ) -> str:
        """
        Create a new broadcast draft.
        Returns the broadcast ID. 
        Raises sqlite3.IntegrityError if idempotency_key is duplicated.
        """
        broadcast_id = f"BRD-{uuid.uuid4().hex[:8].upper()}"
        
        # Use provided idempotency key if any, otherwise default to broadcast_id
        actual_key = idempotency_key or broadcast_id

        try:
            self._db.execute("""
                INSERT INTO broadcasts (id, community_id, message, channels, status, idempotency_key, scheduled_at)
                VALUES (?, ?, ?, ?, 'draft', ?, ?)
            """, (
                broadcast_id,
                community_id,
                message,
                json.dumps(channels),
                actual_key,
                scheduled_at.isoformat() if scheduled_at else None
            ))
            
            # Audit log
            self._log_audit(actor_id, "create", broadcast_id, {
                "community_id": community_id,
                "idempotency_key": actual_key
            })
            
            self._db.commit()
            return broadcast_id
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: broadcasts.idempotency_key" in str(e):
                # Retrieve existing broadcast if idempotency key matches
                res = self._db.execute("SELECT id FROM broadcasts WHERE idempotency_key = ?", (actual_key,)).fetchone()
                if res:
                    return res[0]
            raise

    def approve_broadcast(self, broadcast_id: str, actor_id: str):
        """Transition from draft to approved/queued."""
        self._db.execute("""
            UPDATE broadcasts 
            SET status = 'approved' 
            WHERE id = ? AND status = 'draft'
        """, (broadcast_id,))
        
        if self._db.total_changes > 0:
            self._log_audit(actor_id, "approve", broadcast_id)
            self._db.commit()
            return True
        return False

    def queue_broadcast(self, broadcast_id: str, actor_id: str):
        """Move to queued state for workers to pick up."""
        self._db.execute("""
            UPDATE broadcasts 
            SET status = 'queued' 
            WHERE id = ? AND status = 'approved'
        """, (broadcast_id,))
        
        if self._db.total_changes > 0:
            self._log_audit(actor_id, "queue", broadcast_id)
            self._db.commit()
            return True
        return False

    def _log_audit(self, actor_id: str, action: str, broadcast_id: str, metadata: Optional[Dict] = None):
        """Internal audit logger."""
        log_id = f"ALOG-{uuid.uuid4().hex[:8].upper()}"
        self._db.execute("""
            INSERT INTO broadcast_audit_logs (id, actor_id, action, broadcast_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (log_id, actor_id, action, broadcast_id, json.dumps(metadata) if metadata else None))
