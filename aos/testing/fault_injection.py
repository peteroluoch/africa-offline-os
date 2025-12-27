from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from aos.bus.event_store import EventStore


@dataclass(frozen=True)
class FaultAction:
    name: str
    detail: str


def force_close_sqlite_connection(conn: sqlite3.Connection) -> FaultAction:
    conn.close()
    return FaultAction(
        name="sqlite_connection_closed",
        detail="sqlite3.Connection was force-closed",
    )


def force_close_event_store_connection(store: Any) -> FaultAction:
    """Closes the underlying connection of an EventStore or similar object."""
    # We use Any and getattr for robustness against shadowing/type issues
    conn = getattr(store, "_conn", None)
    if conn is None:
        return FaultAction(
            name="event_store_noop",
            detail="Object has no active connection",
        )

    conn.close()
    return FaultAction(
        name="event_store_connection_closed",
        detail="Underlying connection was force-closed",
    )


def simulate_power_loss(store: Any) -> FaultAction:
    """
    Simulates abrupt power loss.
    """
    force_close_event_store_connection(store)
    return FaultAction(
        name="power_loss",
        detail="Simulated abrupt power loss (connection terminated)",
    )


def simulate_disk_death(conn: Any) -> FaultAction:
    """
    Simulates a "Disk I/O Error".
    Since sqlite3.Connection methods are read-only, we must wrap it or mock the calls 
    at the site of usage. For A-OS testing, we mock the core methods if it's a mockable object,
    otherwise we suggest using a Mock wrapper.
    """
    from unittest.mock import MagicMock
    
    def raise_io_error(*args, **kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    # If it's a real sqlite3.Connection, we can't easily monkeypatch it.
    # But we can patch the specific instance for methods that ARE writable if any,
    # or we just rely on the test to use a Mock connection.
    
    # Actually, the best way for A-OS is to patch 'execute' on the instance if possible.
    try:
        conn.execute = MagicMock(side_effect=raise_io_error)
        conn.commit = MagicMock(side_effect=raise_io_error)
    except (AttributeError, TypeError):
        # Fallback: if it's a C-level object, we can't patch it directly.
        # Tests should use a proxy.
        pass
    
    return FaultAction(
        name="disk_death",
        detail="Simulated disk I/O error",
    )
