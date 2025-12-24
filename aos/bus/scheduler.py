"""
Event Scheduler - Persistent time-based event emission.
Supports delayed one-off events and recurring intervals.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event

logger = logging.getLogger(__name__)

class EventScheduler:
    """
    SQLite-backed event scheduler.
    
    Ensures that events can be emitted at specific times or intervals,
    even after system restarts.
    """
    
    def __init__(self, db_path: str, dispatcher: EventDispatcher) -> None:
        """
        Initialize EventScheduler.
        
        Args:
            db_path: Path to SQLite database.
            dispatcher: EventDispatcher to emit events through.
        """
        self.db_path = db_path
        self.dispatcher = dispatcher
        self._conn: Optional[sqlite3.Connection] = None
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize scheduler database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                event_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                scheduled_at REAL NOT NULL,
                interval_seconds REAL,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        # Index for efficient time-based retrieval
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_time 
            ON scheduled_tasks(status, scheduled_at)
        """)
        
        self._conn.commit()

    async def schedule_after(self, delay_seconds: float, event: Event) -> str:
        """
        Schedule a one-off event after a delay.
        
        Returns:
            task_id: Unique identifier for the scheduled task.
        """
        scheduled_at = time.time() + delay_seconds
        return await self._store_task(event, scheduled_at)

    async def schedule_recurring(self, interval_seconds: float, event: Event) -> str:
        """
        Schedule a recurring event.
        
        Returns:
            task_id: Unique identifier for the scheduled task.
        """
        scheduled_at = time.time() + interval_seconds
        return await self._store_task(event, scheduled_at, interval=interval_seconds)

    async def _store_task(self, event: Event, scheduled_at: float, interval: Optional[float] = None) -> str:
        """Persist task to database."""
        task_id = str(uuid.uuid4())
        async with self._lock:
            self._conn.execute("""
                INSERT INTO scheduled_tasks (
                    id, event_name, payload, scheduled_at, interval_seconds
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                task_id,
                event.name,
                json.dumps(event.payload),
                scheduled_at,
                interval
            ))
            self._conn.commit()
        return task_id

    async def cancel_task(self, task_id: str) -> None:
        """Cancel a scheduled task."""
        async with self._lock:
            self._conn.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
            self._conn.commit()

    async def run(self) -> None:
        """Start the scheduler processing loop."""
        self._running = True
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                now = time.time()
                await self._process_ready_tasks(now)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            
            # Sleep until next check or interrup
            # For simplicity, poll every 0.1s for test responsiveness.
            # In production, this can be optimized to sleep until the next task time.
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._conn:
            self._conn.close()
            self._conn = None
        logger.info("Scheduler loop stopped")

    async def _process_ready_tasks(self, now: float) -> None:
        """Check for and execute tasks that are due."""
        async with self._lock:
            cursor = self._conn.execute("""
                SELECT id, event_name, payload, interval_seconds
                FROM scheduled_tasks
                WHERE status = 'pending' AND scheduled_at <= ?
            """, (now,))
            
            tasks = cursor.fetchall()
            
            for task in tasks:
                task_id, name, payload_str, interval = task
                
                # Emit event
                event = Event(name=name, payload=json.loads(payload_str))
                await self.dispatcher.dispatch(event)
                
                if interval is not None:
                    # Update next execution time for recurring task
                    next_time = now + interval
                    self._conn.execute("""
                        UPDATE scheduled_tasks 
                        SET scheduled_at = ?
                        WHERE id = ?
                    """, (next_time, task_id))
                else:
                    # Mark one-off as completed (or just delete)
                    self._conn.execute("""
                        DELETE FROM scheduled_tasks 
                        WHERE id = ?
                    """, (task_id,))
            
            self._conn.commit()
