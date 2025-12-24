from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional
from aos.bus.events import Event
from aos.bus.event_store import EventStore

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]

class EventDispatcher:
    """
    Async event dispatcher for A-OS kernel communication.
    
    Supports optional persistent journaling via EventStore.
    If a store is provided, events are persisted before dispatch
    and can be recovered after process restarts.
    """
    
    def __init__(self, store: Optional[EventStore] = None):
        """
        Initialize EventDispatcher.
        
        Args:
            store: Optional EventStore for persistent journaling.
        """
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._store = store
        self._lock = asyncio.Lock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register an async handler for a specific event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug(f"Subscribed handler to {event_name}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """Register a handler for ALL events (e.g. logging, streaming)."""
        if "all" not in self._subscribers:
            self._subscribers["all"] = []
        
        if handler not in self._subscribers["all"]:
            self._subscribers["all"].append(handler)
            logger.debug("Subscribed global handler")

    async def dispatch(self, event: Event) -> None:
        """
        Dispatch an event to all registered subscribers.
        
        If a store is present, events are persisted before dispatch.
        Subscribers are executed concurrently as background tasks.
        """
        if self._store:
            await self._store.enqueue(event)
            
        handlers = self._subscribers.get(event.name, [])
        # Add global handlers
        handlers.extend(self._subscribers.get("all", []))
        
        if not handlers:
            # If no handlers and stored, we can consider it completed
            if self._store:
                await self._store.mark_completed(event.id)
            return

        # Execute handlers as independent tasks
        # We wrap them to mark completion in the store after execution
        if self._store:
            asyncio.create_task(self._execute_with_tracking(handlers, event))
        else:
            for handler in handlers:
                asyncio.create_task(self._safe_execute(handler, event))

    async def _execute_with_tracking(self, handlers: List[EventHandler], event: Event) -> None:
        """Execute multiple handlers and track overall success in storage."""
        results = await asyncio.gather(
            *[self._safe_execute_tracked(h, event) for h in handlers],
            return_exceptions=True
        ) or []
        
        # If any handler failed, mark the event as failed in the store
        # Extract exceptions from results
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        if exceptions:
            errmsg = "; ".join(str(e) for e in exceptions)
            await self._store.mark_failed(event.id, errmsg)
        else:
            await self._store.mark_completed(event.id)

    async def _safe_execute_tracked(self, handler: EventHandler, event: Event) -> Optional[Exception]:
        """Execute a single handler and return exception if any."""
        try:
            await handler(event)
            return None
        except Exception as e:
            logger.error(f"Error in handler for {event.name}: {e}", exc_info=True)
            return e

    async def _safe_execute(self, handler: EventHandler, event: Event) -> None:
        """Execute a handler and catch any exceptions (internal use)."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler for {event.name}: {e}", exc_info=True)

    async def recover_pending_events(self) -> int:
        """
        Recover and replay pending events from the store.
        
        Returns:
            Number of events recovered and dispatched.
        """
        if not self._store:
            return 0
        
        pending_events = await self._store.get_pending_events()
        count = 0
        for event in pending_events:
            # Re-dispatch without re-enqueueing (we'll update dispatch to handle this)
            # Actually, we can just call an internal dispatch method
            await self._dispatch_recovered(event)
            count += 1
            
        return count

    async def _dispatch_recovered(self, event: Event) -> None:
        """Internal dispatch for recovered events (skips enqueue)."""
        handlers = self._subscribers.get(event.name, [])
        if not handlers:
            await self._store.mark_completed(event.id)
            return
            
        asyncio.create_task(self._execute_with_tracking(handlers, event))
