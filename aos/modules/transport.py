from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event
from aos.core.module import Module

if TYPE_CHECKING:
    from aos.core.resource import ResourceManager

logger = logging.getLogger("aos.transport")

class TransportModule(Module):
    """
    Transport & Mobility Module.
    Handles route status, vehicle availability, and bookings.
    """

    def __init__(self, dispatcher: EventDispatcher, db_conn: sqlite3.Connection, resource_manager: ResourceManager | None = None):
        self._dispatcher = dispatcher
        self._db = db_conn
        self.resource_manager = resource_manager  # Power awareness

    @property
    def name(self) -> str:
        return "transport"

    async def initialize(self) -> None:
        logger.info("TransportModule initialized")

    async def shutdown(self) -> None:
        pass

    async def handle_event(self, event: Event) -> None:
        pass

    # --- Domain Logic ---

    def list_routes(self) -> list[dict]:
        cursor = self._db.cursor()
        cursor.execute("SELECT id, name, start_point, end_point, base_price FROM routes")
        return [
            {"id": r[0], "name": r[1], "start": r[2], "end": r[3], "price": r[4]}
            for r in cursor.fetchall()
        ]

    def update_vehicle_status(self, plate: str, status: str, route_id: str | None = None) -> bool:
        """Update vehicle availability or route."""
        cursor = self._db.cursor()
        cursor.execute(
            "UPDATE vehicles SET current_status = ?, current_route_id = ?, last_seen = CURRENT_TIMESTAMP WHERE plate_number = ?",
            (status.upper(), route_id, plate.upper())
        )
        self._db.commit()

        if cursor.rowcount > 0:
            # Dispatch event
            # self._dispatcher.dispatch(...)
            return True
        return False

    def get_route_status(self, route_id: str) -> dict:
        """Get status of a route (available vehicles)."""
        cursor = self._db.cursor()
        cursor.execute(
            "SELECT plate_number, current_status FROM vehicles WHERE current_route_id = ? AND current_status != 'OFF_DUTY'",
            (route_id,)
        )
        vehicles = [{"plate": v[0], "status": v[1]} for v in cursor.fetchall()]

        cursor.execute("SELECT name FROM routes WHERE id = ?", (route_id,))
        route_name = cursor.fetchone()

        return {
            "route_id": route_id,
            "route_name": route_name[0] if route_name else "Unknown",
            "vehicles": vehicles
        }
