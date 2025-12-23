"""
Event Store - SQLite-backed persistent event queue.
Provides crash recovery and event replay capabilities.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from aos.bus.events import Event


class EventStore:
    """SQLite-backed persistent event queue with crash recovery."""
    
    def __init__(self, db_path: str, ttl_seconds: int = 86400) -> None:
        """
        Initialize EventStore.
        
        Args:
            db_path: Path to SQLite database file
            ttl_seconds: Time-to-live for completed events (default: 24 hours)
        """
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize database schema."""
        # Create parent directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        
        # Create events table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                event_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                correlation_id TEXT,
                timestamp TEXT NOT NULL,
                source_node TEXT,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                error_message TEXT
            )
        """)
        
        # Create index for efficient queries
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_created 
            ON events(status, created_at)
        """)
        
        self._conn.commit()
    
    async def shutdown(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    async def enqueue(self, event: Event) -> None:
        """
        Persist event to queue.
        
        Args:
            event: Event to persist
        """
        async with self._lock:
            self._conn.execute("""
                INSERT INTO events (
                    id, event_name, payload, correlation_id, 
                    timestamp, source_node, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                event.id,
                event.name,
                json.dumps(event.payload),
                event.correlation_id,
                event.timestamp.isoformat(),
                event.source_node,
                time.time()
            ))
            self._conn.commit()
    
    async def dequeue(self) -> Optional[Event]:
        """
        Dequeue next pending event (atomic operation).
        
        Returns:
            Next pending event or None if queue is empty
        """
        async with self._lock:
            # Get oldest pending event
            cursor = self._conn.execute("""
                SELECT id, event_name, payload, correlation_id, timestamp, source_node
                FROM events
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Mark as processing
            event_id = row[0]
            self._conn.execute("""
                UPDATE events 
                SET status = 'processing'
                WHERE id = ?
            """, (event_id,))
            self._conn.commit()
            
            # Reconstruct event (use object.__setattr__ for frozen dataclass)
            event = Event(
                name=row[1],
                payload=json.loads(row[2]),
                correlation_id=row[3],
            )
            # Manually set the id and timestamp fields
            object.__setattr__(event, 'id', row[0])
            object.__setattr__(event, 'timestamp', datetime.fromisoformat(row[4]))
            object.__setattr__(event, 'source_node', row[5])
            
            return event
    
    async def mark_completed(self, event_id: str) -> None:
        """Mark event as successfully completed."""
        async with self._lock:
            self._conn.execute("""
                UPDATE events 
                SET status = 'completed'
                WHERE id = ?
            """, (event_id,))
            self._conn.commit()
    
    async def mark_failed(self, event_id: str, error_message: str) -> None:
        """Mark event as failed."""
        async with self._lock:
            self._conn.execute("""
                UPDATE events 
                SET status = 'failed', error_message = ?, retry_count = retry_count + 1
                WHERE id = ?
            """, (error_message, event_id))
            self._conn.commit()
    
    async def get_pending_events(self) -> list[Event]:
        """
        Get all pending events (for replay after crash).
        
        Returns:
            List of pending events
        """
        async with self._lock:
            cursor = self._conn.execute("""
                SELECT id, event_name, payload, correlation_id, timestamp, source_node
                FROM events
                WHERE status IN ('pending', 'processing')
                ORDER BY created_at ASC
            """)
            
            events = []
            for row in cursor.fetchall():
                event = Event(
                    name=row[1],
                    payload=json.loads(row[2]),
                    correlation_id=row[3],
                )
                object.__setattr__(event, 'id', row[0])
                object.__setattr__(event, 'timestamp', datetime.fromisoformat(row[4]))
                object.__setattr__(event, 'source_node', row[5])
                events.append(event)
            
            return events
    
    async def cleanup_old_events(self) -> int:
        """
        Delete old completed events based on TTL.
        
        Returns:
            Number of events deleted
        """
        async with self._lock:
            cutoff_time = time.time() - self.ttl_seconds
            
            cursor = self._conn.execute("""
                DELETE FROM events
                WHERE status = 'completed' AND created_at < ?
            """, (cutoff_time,))
            
            self._conn.commit()
            return cursor.rowcount
    
    async def get_queue_depth(self) -> int:
        """Get number of pending events."""
        async with self._lock:
            cursor = self._conn.execute("""
                SELECT COUNT(*) FROM events WHERE status = 'pending'
            """)
            return cursor.fetchone()[0]
    
    async def get_failed_count(self) -> int:
        """Get number of failed events."""
        async with self._lock:
            cursor = self._conn.execute("""
                SELECT COUNT(*) FROM events WHERE status = 'failed'
            """)
            return cursor.fetchone()[0]
