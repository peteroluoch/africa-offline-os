from __future__ import annotations

from aos.testing.fault_injection import (
    force_close_event_store_connection,
    force_close_sqlite_connection,
)

__all__ = [
    "force_close_event_store_connection",
    "force_close_sqlite_connection",
]
