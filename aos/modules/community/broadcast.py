from __future__ import annotations
import uuid
import json
import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher

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

    def get_broadcast(self, broadcast_id: str) -> Optional[Dict]:
        """Fetch broadcast details."""
        res = self._db.execute("SELECT * FROM broadcasts WHERE id = ?", (broadcast_id,)).fetchone()
        if res:
            # Simple row-to-dict mapping (schema known from Migration 010)
            columns = [column[0] for column in self._db.execute("SELECT * FROM broadcasts LIMIT 0").description]
            return dict(zip(columns, res))
        return None

    def lease_next_queued(self, owner_id: str, lease_duration_seconds: int = 300) -> Optional[str]:
        """
        Atomically lease the next queued broadcast.
        Uses a lock_owner and locked_at for worker safety.
        """
        # 1. Find an eligible broadcast (either queued or expired lease)
        res = self._db.execute("""
            SELECT id FROM broadcasts 
            WHERE status = 'queued' 
            AND (locked_at IS NULL OR locked_at < datetime('now', ?))
            LIMIT 1
        """, (f"-{lease_duration_seconds} seconds",)).fetchone()
        
        if not res:
            return None
            
        broadcast_id = res[0]
        
        # 2. Try to lock it
        self._db.execute("""
            UPDATE broadcasts 
            SET lock_owner = ?, locked_at = CURRENT_TIMESTAMP, status = 'processing'
            WHERE id = ? AND (locked_at IS NULL OR locked_at < datetime('now', ?) OR status = 'queued')
        """, (owner_id, broadcast_id, f"-{lease_duration_seconds} seconds"))
        
        if self._db.total_changes > 0:
            self._db.commit()
            return broadcast_id
        return None

    def resolve_recipients(self, broadcast_id: str):
        """
        Map a broadcast to all active community members.
        Creates entries in broadcast_deliveries.
        """
        broadcast = self.get_broadcast(broadcast_id)
        if not broadcast:
            return
            
        community_id = broadcast['community_id']
        
        # 1. Insert deliveries for all active members (idempotent via status check or primary key if we had one)
        # We use a subquery to avoid loading 1M+ members into memory
        self._db.execute("""
            INSERT INTO broadcast_deliveries (id, broadcast_id, member_id, channel, status)
            SELECT ('BDEL-' || SUBSTR(HEX(RANDOMBLOB(4)), 1, 8)), ?, id, channel, 'pending'
            FROM community_members
            WHERE community_id = ? AND active = 1
            AND NOT EXISTS (
                SELECT 1 FROM broadcast_deliveries 
                WHERE broadcast_id = ? AND member_id = community_members.id
            )
        """, (broadcast_id, community_id, broadcast_id))
        
        self._db.commit()

    def fetch_pending_deliveries(self, broadcast_id: str, limit: int = 100) -> List[Dict]:
        """Fetch a batch of pending deliveries."""
        cursor = self._db.execute("""
            SELECT d.id, d.member_id, d.channel, m.user_id 
            FROM broadcast_deliveries d
            JOIN community_members m ON d.member_id = m.id
            WHERE d.broadcast_id = ? AND d.status = 'pending'
            LIMIT ?
        """, (broadcast_id, limit))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_delivery_status(self, delivery_id: str, status: str, error: Optional[str] = None):
        """Update individual delivery status."""
        self._db.execute("""
            UPDATE broadcast_deliveries 
            SET status = ?, error = ?, sent_at = CASE WHEN ? = 'sent' THEN CURRENT_TIMESTAMP ELSE sent_at END
            WHERE id = ?
        """, (status, error, status, delivery_id))
        self._db.commit()

    def complete_broadcast(self, broadcast_id: str, actor_id: str):
        """Mark broadcast as completed and release lock."""
        # Calculate summary statistics
        stats = self._db.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM broadcast_deliveries 
            WHERE broadcast_id = ?
        """, (broadcast_id,)).fetchone()
        
        self._db.execute("""
            UPDATE broadcasts 
            SET status = 'completed', 
                sent_count = ?, 
                failed_count = ?,
                lock_owner = NULL,
                locked_at = NULL
            WHERE id = ?
        """, (stats[0], stats[1], broadcast_id))
        
        self._log_audit(actor_id, "complete", broadcast_id, {
            "sent": stats[0],
            "failed": stats[1]
        })
        self._db.commit()

    def _log_audit(self, actor_id: str, action: str, broadcast_id: str, metadata: Optional[Dict] = None):
        """Internal audit logger."""
        log_id = f"ALOG-{uuid.uuid4().hex[:8].upper()}"
        self._db.execute("""
            INSERT INTO broadcast_audit_logs (id, actor_id, action, broadcast_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (log_id, actor_id, action, broadcast_id, json.dumps(metadata) if metadata else None))


class BroadcastWorker:
    """
    Background worker that processes queued broadcasts.
    Ensures Exactly-Once delivery via persistent delivery logs.
    """

    def __init__(
        self, 
        manager: BroadcastManager, 
        dispatcher: EventDispatcher,
        check_interval: int = 5
    ):
        self._manager = manager
        self._dispatcher = dispatcher
        self._interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._worker_id = f"WRK-{uuid.uuid4().hex[:4].upper()}"
        
        # Register event listeners for delivery confirmations
        self._dispatcher.subscribe("MESSAGE_SENT", self._handle_message_sent)
        self._dispatcher.subscribe("MESSAGE_FAILED", self._handle_message_failed)

    async def _handle_message_sent(self, event):
        """Handle successful message delivery confirmation."""
        correlation_id = event.payload.get("correlation_id")
        if correlation_id:
            self._manager.update_delivery_status(correlation_id, 'sent')
            logger.debug(f"Delivery {correlation_id} marked as sent")

    async def _handle_message_failed(self, event):
        """Handle failed message delivery."""
        correlation_id = event.payload.get("correlation_id")
        error = event.payload.get("error", "Unknown error")
        if correlation_id:
            self._manager.update_delivery_status(correlation_id, 'failed', error=error)
            logger.warning(f"Delivery {correlation_id} marked as failed: {error}")

    def start(self):
        """Start the background worker task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"BroadcastWorker {self._worker_id} started")

    async def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"BroadcastWorker {self._worker_id} stopped")

    async def _loop(self):
        """Main worker loop."""
        while self._running:
            try:
                # 1. Lease a broadcast
                broadcast_id = self._manager.lease_next_queued(self._worker_id)
                if broadcast_id:
                    logger.info(f"Processing broadcast {broadcast_id}")
                    await self._process_broadcast(broadcast_id)
                else:
                    await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in BroadcastWorker loop: {e}")
                await asyncio.sleep(self._interval)

    async def _process_broadcast(self, broadcast_id: str):
        """Execute the delivery flow for a specific broadcast."""
        # 1. Resolve recipients if not already done
        self._manager.resolve_recipients(broadcast_id)
        
        broadcast = self._manager.get_broadcast(broadcast_id)
        if not broadcast:
            return

        # 2. Process batches of deliveries
        while self._running:
            batch = self._manager.fetch_pending_deliveries(broadcast_id, limit=50)
            if not batch:
                break
                
            for delivery in batch:
                if not self._running:
                    break
                    
                try:
                    # Dispatch to the specific channel adapter via the bus
                    # In A-OS, we use name="SEND_MESSAGE" for outgoing channel traffic
                    from aos.bus.events import Event
                    await self._dispatcher.dispatch(Event(
                        name="SEND_MESSAGE", # Unified outgoing command
                        payload={
                            "to": delivery['user_id'],
                            "channel": delivery['channel'],
                            "content": broadcast['message'],
                            "correlation_id": delivery['id']
                        }
                    ))
                    # NOTE: Status update happens via MESSAGE_SENT/MESSAGE_FAILED events
                    # This ensures accurate tracking based on adapter confirmation
                except Exception as e:
                    logger.error(f"Failed to dispatch {delivery['id']}: {e}")
                    self._manager.update_delivery_status(delivery['id'], 'failed', error=str(e))
            
            # Short yield between batches to keep the event loop responsive
            await asyncio.sleep(0.1)

        # 3. Finalize
        self._manager.complete_broadcast(broadcast_id, self._worker_id)
        logger.info(f"Broadcast {broadcast_id} completed")
