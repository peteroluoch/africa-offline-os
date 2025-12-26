from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aos.bus.event_store import EventStore
from aos.bus.events import Event
from aos.testing.fault_injection import force_close_event_store_connection


class TestFaultInjection:
    @pytest.mark.asyncio
    async def test_fault_injection_can_force_close_event_store_connection(
        self,
        tmp_path: Path,
    ) -> None:
        db_path = str(tmp_path / "fault.db")
        store = EventStore(db_path)
        await store.initialize()

        force_close_event_store_connection(store)

        with pytest.raises(sqlite3.ProgrammingError):
            await store.get_queue_depth()

    @pytest.mark.asyncio
    async def test_fault_injection_allows_recovery_via_restart(
        self,
        tmp_path: Path,
    ) -> None:
        db_path = str(tmp_path / "fault_recover.db")

        store1 = EventStore(db_path)
        await store1.initialize()
        await store1.enqueue(Event(name="test.fault", payload={"x": 1}))

        force_close_event_store_connection(store1)

        store2 = EventStore(db_path)
        await store2.initialize()
        try:
            pending = await store2.get_pending_events()
            assert len(pending) == 1
            assert pending[0].name == "test.fault"
            assert pending[0].payload["x"] == 1
        finally:
            await store2.shutdown()
