import logging
import json
import uuid
from typing import Dict, Any
from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event
from aos.core.vehicles.interface import VehicleInterface
from aos.db.repository import MessageRetryRepository
from aos.db.models import MessageRetryDTO

logger = logging.getLogger("aos.vehicles.manager")

class OutboundMessageManager:
    """
    Orchestrates outbound communication across all vehicles.
    Handles persistent retries for offline resilience (Prompt 14).
    """
    
    def __init__(self, dispatcher: EventDispatcher, retry_repo: MessageRetryRepository):
        self.dispatcher = dispatcher
        self.retry_repo = retry_repo
        self.vehicles: Dict[str, VehicleInterface] = {}
        
        # Subscribe to outbound sending events
        self.dispatcher.subscribe("outbound_send", self.handle_send_request)

    def register_vehicle(self, vehicle: VehicleInterface):
        """Register a communication channel (e.g., Telegram, SMS)."""
        self.vehicles[vehicle.vehicle_type] = vehicle
        logger.info(f"Registered vehicle: {vehicle.vehicle_type}")

    async def handle_send_request(self, event: Event):
        """Standardized handler for outbound_send events."""
        payload = event.payload
        to = str(payload.get("to"))
        vehicle_type = payload.get("vehicle_type")
        message = payload.get("message")
        community_id = payload.get("community_id", "GLOBAL")
        metadata = payload.get("metadata", {})

        if vehicle_type not in self.vehicles:
            logger.error(f"No vehicle registered for type: {vehicle_type}")
            await self._queue_for_retry(community_id, vehicle_type, to, message, metadata)
            return

        vehicle = self.vehicles[vehicle_type]
        success = False
        try:
            success = await vehicle.send_message(to, message, metadata=metadata)
        except Exception as e:
            logger.error(f"Error sending message via {vehicle_type}: {e}")
        
        if not success:
            logger.warning(f"Message delivery failed to {to} via {vehicle_type}. Queuing for retry.")
            await self._queue_for_retry(community_id, vehicle_type, to, message, metadata)

    async def _queue_for_retry(self, community_id: str, vehicle_type: str, to: str, content: str, metadata: dict):
        """Persist failed message to retry queue."""
        try:
            retry_log = MessageRetryDTO(
                id=str(uuid.uuid4()),
                community_id=community_id,
                vehicle_type=vehicle_type,
                vehicle_identity=to,
                content=content,
                metadata=json.dumps(metadata) if metadata else None
            )
            self.retry_repo.save(retry_log)
        except Exception as e:
            logger.critical(f"FATAL: Could not queue message for retry: {e}")

    async def process_retries(self):
        """Background task to flush the retry queue when online."""
        pending = self.retry_repo.list_pending()
        if not pending:
            return

        logger.info(f"Processing {len(pending)} queued messages...")
        for item in pending:
            if item.vehicle_type in self.vehicles:
                vehicle = self.vehicles[item.vehicle_type]
                try:
                    metadata = json.loads(item.metadata) if item.metadata else {}
                    success = await vehicle.send_message(item.vehicle_identity, item.content, metadata=metadata)
                    if success:
                        self.retry_repo.delete(item.id)
                        logger.info(f"Successfully retried message {item.id}")
                    else:
                        self.retry_repo.increment_retry(item.id)
                except Exception as e:
                    logger.error(f"Retry failed for {item.id}: {e}")
                    self.retry_repo.increment_retry(item.id)
