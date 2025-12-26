"""
Module Base Contract - Foundation for all business logic modules.
Defines the interface that all business logic modules must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from aos.bus.events import Event


class Module(ABC):
    """
    Base module for business logic components.
    
    All business logic modules must inherit from this class and implement
    the required methods. Modules are event-driven and integrate with the
    EventDispatcher.
    
    Example:
        class UserModule(Module):
            @property
            def name(self) -> str:
                return "user.module"
            
            async def initialize(self) -> None:
                self.db = await connect_db()
            
            async def shutdown(self) -> None:
                await self.db.close()
            
            async def handle_event(self, event: Event) -> None:
                if event.name == "user.created":
                    await self.send_welcome_email(event.payload)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique module identifier.
        
        Returns:
            Module name (e.g., "user.module", "payment.module")
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize module resources.
        
        Called once during application startup. Use this to:
        - Establish database connections
        - Load configuration
        - Subscribe to events
        - Initialize caches
        
        Raises:
            RuntimeError: If initialization fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown module.
        
        Called once during application shutdown. Use this to:
        - Close database connections
        - Flush caches
        - Complete pending operations
        
        This method must be idempotent - calling it multiple times
        should be safe and not raise errors.
        """
        pass

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """
        Process an event.
        
        This method is called by the EventDispatcher when an event
        the module has subscribed to is emitted.
        
        Args:
            event: Event to process
        
        Raises:
            Exception: If event processing fails
        """
        pass
