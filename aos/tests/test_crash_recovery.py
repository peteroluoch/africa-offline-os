"""
Crash Recovery Tests - PHASE 1 BATCH 3
Verifies that the Event Bus can recover and replay events after a process failure.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from aos.bus.dispatcher import EventDispatcher
from aos.bus.event_store import EventStore
from aos.bus.events import Event


class TestCrashRecovery:
    """Test suite for Event Bus durability and crash recovery."""

    @pytest.mark.asyncio
    async def test_persistent_dispatch_flow(self, tmp_path: Path) -> None:
        """Dispatcher must journal events to EventStore before processing."""
        db_path = str(tmp_path / "bus.db")
        store = EventStore(db_path)
        await store.initialize()

        dispatcher = EventDispatcher(store=store)

        # Track handled events
        handled = []
        async def handler(event: Event):
            handled.append(event)

        dispatcher.subscribe("test.event", handler)

        # Dispatch event
        event = Event(name="test.event", payload={"data": "test"})
        await dispatcher.dispatch(event)

        # Wait for async handler
        await asyncio.sleep(0.1)

        # Verify event was handled
        assert len(handled) == 1

        # Verify event was marked as completed in store
        # (Status 'completed' means it worked)
        pending = await store.get_pending_events()
        assert len(pending) == 0, "Event must be marked as completed in store"

        await store.shutdown()

    @pytest.mark.asyncio
    async def test_recovery_on_startup(self, tmp_path: Path) -> None:
        """Dispatcher must be able to replay pending events from store."""
        db_path = str(tmp_path / "recovery.db")

        # Session 1: Enqueue event but "crash" before processing
        store1 = EventStore(db_path)
        await store1.initialize()
        event = Event(name="recoverable.event", payload={"id": 123})
        await store1.enqueue(event)
        await store1.shutdown()

        # Session 2: Boot dispatcher with that store
        store2 = EventStore(db_path)
        await store2.initialize()
        dispatcher = EventDispatcher(store=store2)

        handled = []
        async def handler(e: Event):
            handled.append(e)

        dispatcher.subscribe("recoverable.event", handler)

        # Trigger recovery
        recovered_count = await dispatcher.recover_pending_events()
        assert recovered_count == 1

        # Wait for processing
        await asyncio.sleep(0.1)

        assert len(handled) == 1
        assert handled[0].payload["id"] == 123

        # Verify it's now completed
        pending = await store2.get_pending_events()
        assert len(pending) == 0

        await store2.shutdown()

    @pytest.mark.asyncio
    async def test_failure_handling_durability(self, tmp_path: Path) -> None:
        """Dispatcher must mark events as failed if handlers crash."""
        db_path = str(tmp_path / "failure.db")
        store = EventStore(db_path)
        await store.initialize()

        dispatcher = EventDispatcher(store=store)

        async def failing_handler(event: Event):
            raise RuntimeError("Handler explosed!")

        dispatcher.subscribe("explode.event", failing_handler)

        event = Event(name="explode.event", payload={})
        await dispatcher.dispatch(event)

        # Wait for execution
        await asyncio.sleep(0.1)

        # Verify it's marked as failed in store
        # Since EventStore doesn't have a direct 'get_failed_events' yet,
        # we check the failed count.
        assert await store.get_failed_count() == 1

        await store.shutdown()
