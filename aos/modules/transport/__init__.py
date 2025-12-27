"""
Transport & Mobility Module v2.
Focuses on Mobility Intelligence through Zones, Signals, and Availability.
"""
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict

from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event
from aos.core.module import Module
from aos.db.models import (
    TransportZoneDTO, TrafficSignalDTO, TransportAvailabilityDTO
)
from aos.db.repository import (
    TransportZoneRepository, TrafficSignalRepository, TransportAvailabilityRepository
)

logger = logging.getLogger("aos.transport")

class TransportModule(Module):
    """
    Transport Module v2.
    Implements a fluid infrastructure for local mobility intelligence.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        db_conn: sqlite3.Connection,
        resource_manager=None
    ):
        self._dispatcher = dispatcher
        self._db = db_conn
        self._resource_manager = resource_manager
        
        # Repositories
        self._zones = TransportZoneRepository(db_conn)
        self._signals = TrafficSignalRepository(db_conn)
        self._availabilities = TransportAvailabilityRepository(db_conn)

    @property
    def name(self) -> str:
        return "transport"

    async def initialize(self) -> None:
        logger.info("TransportModule v2 initialized")

    async def shutdown(self) -> None:
        pass

    async def handle_event(self, event: Event) -> None:
        pass

    # --- Core Domain Methods (v2) ---

    def register_zone(
        self,
        name: str,
        type: str,
        location_scope: Optional[str] = None
    ) -> str:
        """Register a new transport zone (road, stage, junction, area)."""
        zone_id = str(uuid.uuid4())
        zone = TransportZoneDTO(
            id=zone_id,
            name=name,
            type=type,
            location_scope=location_scope
        )
        self._zones.save(zone)
        return zone_id

    def report_traffic_signal(
        self,
        zone_id: str,
        state: str,
        source: str,
        expires_in_minutes: int = 30
    ) -> bool:
        """Report traffic state for a zone."""
        # Validate zone
        if not self._zones.get_by_id(zone_id):
            return False
            
        signal_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        signal = TrafficSignalDTO(
            id=signal_id,
            zone_id=zone_id,
            state=state.lower(),
            source=source,
            expires_at=expires_at
        )
        self._signals.save(signal)
        return True

    def report_availability(
        self,
        zone_id: str,
        destination: str,
        state: str,
        source: str,
        expires_in_minutes: int = 60
    ) -> bool:
        """Report vehicle availability to a destination from a zone."""
        # Validate zone
        if not self._zones.get_by_id(zone_id):
            return False
            
        avail_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        availability = TransportAvailabilityDTO(
            id=avail_id,
            zone_id=zone_id,
            destination=destination,
            availability_state=state.lower(),
            reported_by=source,
            expires_at=expires_at
        )
        self._availabilities.save(availability)
        return True

    def get_group(self, zone_id: str) -> Optional[TransportZoneDTO]:
        """Shim to match repository interface style if needed."""
        return self._zones.get_by_id(zone_id)

    def get_zone_intelligence(self, zone_id: str) -> dict:
        """
        Aggregate recent signals and availability for a zone.
        Calculates a consensus state based on confidence scores.
        """
        zone = self._zones.get_by_id(zone_id)
        if not zone:
            return {}

        now = datetime.utcnow()
        
        # 1. Fetch active signals
        all_signals = self._signals.list_all()
        active_signals = [
            s for s in all_signals 
            if s.zone_id == zone_id and (s.expires_at is None or s.expires_at > now)
        ]
        
        # 2. Fetch active availabilities
        all_avail = self._availabilities.list_all()
        active_avail = [
            a for a in all_avail 
            if a.zone_id == zone_id and (a.expires_at is None or a.expires_at > now)
        ]
        
        # Aggregate signal consensus
        state_scores = {"flowing": 0.0, "slow": 0.0, "blocked": 0.0}
        for s in active_signals:
            if s.state in state_scores:
                state_scores[s.state] += s.confidence_score
        
        current_state = max(state_scores, key=state_scores.get) if any(state_scores.values()) else "unknown"
        
        return {
            "zone_id": zone_id,
            "zone_name": zone.name,
            "type": zone.type,
            "current_state": current_state,
            "confidence": state_scores.get(current_state, 0.0),
            "signals": [s.model_dump() for s in active_signals],
            "availability": [a.model_dump() for a in active_avail]
        }

    def discover_zones(
        self,
        location_scope: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> List[TransportZoneDTO]:
        """Find transport zones by location or type."""
        all_zones = self._zones.list_all()
        filtered = all_zones
        
        if location_scope:
            filtered = [z for z in filtered if z.location_scope and location_scope.lower() in z.location_scope.lower()]
            
        if type_filter:
            filtered = [z for z in filtered if z.type == type_filter]
            
        return filtered

    # --- Backward Compatibility Shims ---

    def list_routes(self) -> List[Dict]:
        """Shim: Map zones (type='road') to legacy routes."""
        zones = self.discover_zones(type_filter="road")
        return [
            {"id": z.id, "name": z.name, "start": "", "end": "", "price": 0.0}
            for z in zones
        ]

    def get_route_status(self, route_id: str) -> Dict:
        """Shim: Map zone intelligence to legacy route status."""
        intel = self.get_zone_intelligence(route_id)
        if not intel:
            return {"route_id": route_id, "route_name": "Unknown", "vehicles": []}
            
        # Map intelligence to "vehicles" for USSD compatibility
        # We simulate "vehicles" based on availability state
        vehicles = []
        for avail in intel["availability"]:
            vehicles.append({
                "plate": f"To: {avail['destination']}",
                "status": avail["availability_state"].upper()
            })
            
        return {
            "route_id": route_id,
            "route_name": intel["zone_name"],
            "vehicles": vehicles,
            "traffic_state": intel["current_state"]
        }
