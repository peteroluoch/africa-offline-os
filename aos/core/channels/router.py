from __future__ import annotations
from abc import ABC, abstractmethod
from aos.core.channels.base import ChannelRequest, ChannelResponse
from aos.core.channels.ussd import USSDSession


class MenuNode(ABC):
    """A single node in a USSD menu tree."""
    
    @abstractmethod
    def render(self, session: USSDSession) -> str:
        """Render the menu text."""
        pass
    
    @abstractmethod
    def handle(self, session: USSDSession, user_input: str) -> str | None:
        """Process input and return key for the next node (or None to end)."""
        pass


class Router:
    """Routes channel requests to the appropriate module/handler."""
    
    def __init__(self):
        self._handlers = {} # Map of service_code/shortcode to handler
    
    def register(self, identifier: str, handler: Any):
        self._handlers[identifier] = handler
    
    def get_handler(self, identifier: str) -> Any:
        return self._handlers.get(identifier)
