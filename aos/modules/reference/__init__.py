from __future__ import annotations
import asyncio
from aos.core.module import Module
from aos.bus.events import Event
from aos.bus.dispatcher import EventDispatcher

class ReferenceModule(Module):
    """
    Reference implementation of a Vehicle Module.
    Demonstrates Hexagonal Architecture compliance.
    """
    
    def __init__(self, dispatcher: EventDispatcher):
        self.dispatcher = dispatcher
        
    @property
    def name(self) -> str:
        return "system.reference"

    async def initialize(self) -> None:
        """Register listeners."""
        # Subscribe to ping events
        self.dispatcher.subscribe("system.ping", self.handle_event)

    async def shutdown(self) -> None:
        """Cleanup resources."""
        pass

    async def handle_event(self, event: Event) -> None:
        """Process system events."""
        if event.name == "system.ping":
            await self._handle_ping(event)

    async def _handle_ping(self, event: Event) -> None:
        """PONG logic."""
        response_payload = {
            "nonce": event.payload.get("nonce"),
            "status": "ok",
            "source": self.name
        }
        
        pong = Event(name="system.pong", payload=response_payload, correlation_id=event.id)
        
        # Dispatch response back to bus
        # Note: dispatch() is async
        await self.dispatcher.dispatch(pong)
