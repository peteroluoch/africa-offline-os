from __future__ import annotations

import sqlite3
from dataclasses import dataclass

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


def force_close_event_store_connection(store: EventStore) -> FaultAction:
    conn: sqlite3.Connection | None = store._conn
    if conn is None:
        return FaultAction(
            name="event_store_noop",
            detail="EventStore has no active connection",
        )

    conn.close()
    return FaultAction(
        name="event_store_connection_closed",
        detail="EventStore underlying sqlite connection was force-closed",
    )
