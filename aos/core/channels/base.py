from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChannelType(str, Enum):
    USSD = "ussd"
    SMS = "sms"
    WHATSAPP = "whatsapp"


@dataclass
class ChannelRequest:
    """Standardized request from any communication channel."""
    session_id: str
    sender: str
    content: str
    channel_type: str
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelResponse:
    """Standardized response to any communication channel."""
    content: str
    session_active: bool = False
    metadata: dict[str, Any] | None = None


class ChannelAdapter(ABC):
    """Abstract base class for all channel adapters."""

    @abstractmethod
    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        """Parse raw provider payload into a standard ChannelRequest."""
        pass

    @abstractmethod
    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        """Format standard ChannelResponse into provider-specific format."""
        pass

    @abstractmethod
    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        """Send an outbound message (SMS/WhatsApp)."""
        pass

    @abstractmethod
    def get_channel_type(self) -> str:
        """Return the channel type identifier."""
        pass


class ChannelGateway(ABC):
    """Abstract base class for external API gateways (AT, Twilio)."""

    @abstractmethod
    async def send(self, to: str, message: str, **kwargs) -> dict[str, Any]:
        """Send a message via the external API."""
        pass

    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> str:
        """Get status of a sent message."""
        pass
