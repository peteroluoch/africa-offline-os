import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List
from aos.bus.events import Event

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]

class EventDispatcher:
    """
    In-memory async event dispatcher for A-OS kernel communication.
    
    Provides thread-safe subscription and dispatching of domain events.
    Subscribers are executed as independent asyncio tasks to ensure isolation.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register an async handler for a specific event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug(f"Subscribed handler to {event_name}")

    async def dispatch(self, event: Event) -> None:
        """
        Dispatch an event to all registered subscribers.
        
        Subscribers are executed concurrently as background tasks.
        Failures in one handler do not affect others.
        """
        handlers = self._subscribers.get(event.name, [])
        if not handlers:
            return

        # Execute handlers as independent tasks for isolation
        for handler in handlers:
            asyncio.create_task(self._safe_execute(handler, event))

    async def _safe_execute(self, handler: EventHandler, event: Event) -> None:
        """Execute a handler and catch any exceptions to prevent bus disruption."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler for {event.name}: {e}", exc_info=True)
