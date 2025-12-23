"""
Event Persistence Tests - PHASE 1 BATCH 2
Tests for SQLite-backed event queue with crash recovery.

Following TDD: These tests define the EventStore requirements.
"""
from __future__ import annotations

import asyncio
import sqlite3
import time
from pathlib import Path

import pytest

from aos.bus.events import Event
from aos.bus.event_store import EventStore


class TestEventStorePersistence:
    """Test that events are persisted to SQLite."""

    @pytest.mark.asyncio
    async def test_store_persists_event(self, tmp_path: Path) -> None:
        """EventStore must persist events to SQLite."""
        db_path = tmp_path / "events.db"
        store = EventStore(str(db_path))
        await store.initialize()
        
        try:
            # Create and store event
            event = Event(
                name="test.event",
                payload={"data": "test"},
                correlation_id="test-123"
            )
            await store.enqueue(event)
            
            # Verify event is in database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT * FROM events WHERE id = ?", (event.id,))
            row = cursor.fetchone()
            conn.close()
            
            assert row is not None, "Event must be persisted to database"
            assert row[1] == "test.event", "Event name must match"
            assert row[3] == "test-123", "Correlation ID must match"
        finally:
            await store.shutdown()

    @pytest.mark.asyncio
    async def test_dequeue_removes_event(self, tmp_path: Path) -> None:
        """Dequeuing an event must mark it as completed."""
        db_path = tmp_path / "events.db"
        store = EventStore(str(db_path))
        await store.initialize()
        
        try:
            # Store event
            event = Event(name="test.event", payload={"data": "test"})
            await store.enqueue(event)
            
            # Dequeue event
            dequeued = await store.dequeue()
            assert dequeued is not None
            assert dequeued.id == event.id
            
            # Mark as completed
            await store.mark_completed(dequeued.id)
            
            # Verify status is updated
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(
                "SELECT status FROM events WHERE id = ?", 
                (event.id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            assert row[0] == "completed", "Event must be marked as completed"
        finally:
            await store.shutdown()


class TestEventStoreCrashRecovery:
    """Test crash recovery and event replay."""

    @pytest.mark.asyncio
    async def test_replay_pending_events_after_crash(self, tmp_path: Path) -> None:
        """EventStore must replay pending events after restart."""
        db_path = tmp_path / "events.db"
        
        # First session: Store events
        store1 = EventStore(str(db_path))
        await store1.initialize()
        
        event1 = Event(name="test.event1", payload={"data": "1"})
        event2 = Event(name="test.event2", payload={"data": "2"})
        await store1.enqueue(event1)
        await store1.enqueue(event2)
        
        # Simulate crash (don't call shutdown)
        del store1
        
        # Second session: Replay events
        store2 = EventStore(str(db_path))
        await store2.initialize()
        
        try:
            # Get pending events
            pending = await store2.get_pending_events()
            
            assert len(pending) == 2, "Must replay all pending events"
            assert pending[0].name == "test.event1"
            assert pending[1].name == "test.event2"
        finally:
            await store2.shutdown()

    @pytest.mark.asyncio
    async def test_no_duplicate_processing(self, tmp_path: Path) -> None:
        """Events must not be processed twice."""
        db_path = tmp_path / "events.db"
        store = EventStore(str(db_path))
        await store.initialize()
        
        try:
            # Store event
            event = Event(name="test.event", payload={"data": "test"})
            await store.enqueue(event)
            
            # Dequeue twice
            first = await store.dequeue()
            second = await store.dequeue()
            
            assert first is not None
            assert second is None, "Same event must not be dequeued twice"
        finally:
            await store.shutdown()


class TestEventStoreTTL:
    """Test automatic cleanup of old events."""

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, tmp_path: Path) -> None:
        """Old completed events must be auto-deleted."""
        db_path = tmp_path / "events.db"
        store = EventStore(str(db_path), ttl_seconds=1)  # 1 second TTL
        await store.initialize()
        
        try:
            # Store and complete event
            event = Event(name="test.event", payload={"data": "test"})
            await store.enqueue(event)
            
            dequeued = await store.dequeue()
            await store.mark_completed(dequeued.id)
            
            # Wait for TTL
            await asyncio.sleep(1.5)
            
            # Run cleanup
            deleted_count = await store.cleanup_old_events()
            
            assert deleted_count == 1, "Old event must be deleted"
            
            # Verify event is gone
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 0, "Database must be empty after cleanup"
        finally:
            await store.shutdown()


class TestEventStoreMetrics:
    """Test event queue metrics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_queue_depth(self, tmp_path: Path) -> None:
        """EventStore must report queue depth."""
        db_path = tmp_path / "events.db"
        store = EventStore(str(db_path))
        await store.initialize()
        
        try:
            # Initially empty
            depth = await store.get_queue_depth()
            assert depth == 0
            
            # Add events
            await store.enqueue(Event(name="test.1", payload={}))
            await store.enqueue(Event(name="test.2", payload={}))
            
            depth = await store.get_queue_depth()
            assert depth == 2, "Queue depth must reflect pending events"
        finally:
            await store.shutdown()

    @pytest.mark.asyncio
    async def test_get_failed_events_count(self, tmp_path: Path) -> None:
        """EventStore must track failed events."""
        db_path = tmp_path / "events.db"
        store = EventStore(str(db_path))
        await store.initialize()
        
        try:
            # Store event
            event = Event(name="test.event", payload={})
            await store.enqueue(event)
            
            # Mark as failed
            dequeued = await store.dequeue()
            await store.mark_failed(dequeued.id, "Test error")
            
            # Check failed count
            failed_count = await store.get_failed_count()
            assert failed_count == 1, "Must track failed events"
        finally:
            await store.shutdown()
