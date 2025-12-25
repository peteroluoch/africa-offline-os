"""
AgriModule - Agricultural Management Lighthouse.
Handles farmer registration, harvest recording, and inventory tracking.
"""
from __future__ import annotations
import sqlite3
import logging
from typing import List, Optional
from aos.core.module import Module
from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event
from aos.db.repository import FarmerRepository, HarvestRepository, CropRepository
from aos.db.models import FarmerDTO, HarvestDTO, CropDTO

logger = logging.getLogger("aos.agri")

class AgriModule(Module):
    """
    Business logic for the Agricultural domain.
    """
    
    def __init__(self, dispatcher: EventDispatcher, db_conn: sqlite3.Connection):
        self._dispatcher = dispatcher
        self._db = db_conn
        self._farmers = FarmerRepository(db_conn)
        self._harvests = HarvestRepository(db_conn)
        self._crops = CropRepository(db_conn)

    @property
    def name(self) -> str:
        return "agri"

    async def initialize(self) -> None:
        """Register the module with the event bus."""
        # The module is primarily active (produces events)
        # But it could listen for mesh-syndicated agri events in the future
        logger.info("AgriModule initialized")

    async def shutdown(self) -> None:
        """Cleanup module resources."""
        pass

    async def handle_event(self, event: Event) -> None:
        """Handle incoming events."""
        # For now, AgriModule is mostly an event originator
        pass

    # --- Domain Logic ---

    async def register_farmer(self, farmer: FarmerDTO) -> None:
        """Register a new farmer in the local node."""
        self._farmers.save(farmer)
        await self._dispatcher.dispatch(Event(
            name="agri.farmer_registered",
            payload=farmer.model_dump()
        ))
        logger.info(f"Farmer registered: {farmer.name} ({farmer.id})")

    async def record_harvest(self, harvest: HarvestDTO) -> None:
        """Record a new harvest for a farmer."""
        # Verify farmer and crop exist (Simplified for now)
        self._harvests.save(harvest)
        await self._dispatcher.dispatch(Event(
            name="agri.harvest_recorded",
            payload=harvest.model_dump()
        ))
        logger.info(f"Harvest recorded for farmer {harvest.farmer_id}: {harvest.quantity}{harvest.unit}")

    def get_farmer_harvests(self, farmer_id: str) -> List[HarvestDTO]:
        """Retrieve all harvests for a specific farmer."""
        # This is a bit inefficient if we have millions of harvests, 
        # but suitable for an A-OS Edge Node.
        all_harvests = self._harvests.list_all()
        return [h for h in all_harvests if h.farmer_id == farmer_id]

    def list_all_farmers(self) -> List[FarmerDTO]:
        """List all farmers registered on this node."""
        return self._farmers.list_all()

    def list_crops(self) -> List[CropDTO]:
        """List supported crop types."""
        return self._crops.list_all()
