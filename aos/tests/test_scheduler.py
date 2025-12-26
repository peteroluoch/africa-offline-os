"""
Event Scheduler Tests - PHASE 1 BATCH 3
Verifies that the Event Scheduler can handle one-off and recurring events with persistence.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event
from aos.bus.scheduler import EventScheduler


class TestEventScheduler:
    """Test suite for persistent Event Scheduler."""

    @pytest.mark.asyncio
    async def test_schedule_one_off_event(self, tmp_path: Path) -> None:
        """Scheduler must emit a one-off event after a delay."""
        db_path = str(tmp_path / "scheduler.db")
        dispatcher = EventDispatcher()
        scheduler = EventScheduler(db_path, dispatcher)
        await scheduler.initialize()

        handled = []
        async def handler(event: Event):
            handled.append(event)

        dispatcher.subscribe("delayed.event", handler)

        # Schedule event for 0.5s from now
        event = Event(name="delayed.event", payload={"test": "one-off"})
        await scheduler.schedule_after(0.5, event)

        # Start scheduler loop
        task = asyncio.create_task(scheduler.run())

        try:
            # Wait for event
            await asyncio.sleep(1.0)
            assert len(handled) == 1
            assert handled[0].payload["test"] == "one-off"
        finally:
            await scheduler.stop()
            task.cancel()

    @pytest.mark.asyncio
    async def test_schedule_recurring_event(self, tmp_path: Path) -> None:
        """Scheduler must emit events at regular intervals."""
        db_path = str(tmp_path / "recurring.db")
        dispatcher = EventDispatcher()
        scheduler = EventScheduler(db_path, dispatcher)
        await scheduler.initialize()

        handled = []
        async def handler(event: Event):
            handled.append(event)

        dispatcher.subscribe("tick.event", handler)

        # Schedule recurring event every 0.3s
        event = Event(name="tick.event", payload={})
        await scheduler.schedule_recurring(0.3, event)

        # Start scheduler loop
        task = asyncio.create_task(scheduler.run())

        try:
            # Wait for at least 3 ticks (0.3, 0.6, 0.9)
            await asyncio.sleep(1.2)
            assert len(handled) >= 3
        finally:
            await scheduler.stop()
            task.cancel()

    @pytest.mark.asyncio
    async def test_scheduler_persistence(self, tmp_path: Path) -> None:
        """Tasks must survive scheduler restart."""
        db_path = str(tmp_path / "persistent_sched.db")
        dispatcher = EventDispatcher()

        # Session 1: Schedule task and "crash"
        scheduler1 = EventScheduler(db_path, dispatcher)
        await scheduler1.initialize()
        event = Event(name="reboot.event", payload={"id": 999})
        await scheduler1.schedule_after(2.0, event) # Long enough to not trigger
        await scheduler1.stop()

        # Session 2: Restore and wait
        scheduler2 = EventScheduler(db_path, dispatcher)
        await scheduler2.initialize()

        handled = []
        async def handler(e: Event):
            handled.append(e)
        dispatcher.subscribe("reboot.event", handler)

        task = asyncio.create_task(scheduler2.run())

        try:
            # Wait for the task that was scheduled in Session 1
            await asyncio.sleep(2.5)
            assert len(handled) == 1
            assert handled[0].payload["id"] == 999
        finally:
            await scheduler2.stop()
            task.cancel()

    @pytest.mark.asyncio
    async def test_cancel_scheduled_event(self, tmp_path: Path) -> None:
        """Scheduler must support canceling a task by name/type."""
        db_path = str(tmp_path / "cancel.db")
        dispatcher = EventDispatcher()
        scheduler = EventScheduler(db_path, dispatcher)
        await scheduler.initialize()

        handled = []
        async def handler(e: Event):
            handled.append(e)
        dispatcher.subscribe("canceled.event", handler)

        # Schedule and then cancel
        event = Event(name="canceled.event", payload={})
        task_id = await scheduler.schedule_after(1.0, event)
        await scheduler.cancel_task(task_id)

        task = asyncio.create_task(scheduler.run())

        try:
            await asyncio.sleep(1.5)
            assert len(handled) == 0, "Canceled task must not execute"
        finally:
            await scheduler.stop()
            task.cancel()
