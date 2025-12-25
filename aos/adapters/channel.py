from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ChannelMessage:
    """Represents a message sent or received through a channel."""
    sender: str  # Phone number or session ID
    recipient: str  # Phone number or shortcode
    content: str
    timestamp: datetime
    metadata: dict[str, Any] | None = None


@dataclass
class ChannelRequest:
    """Represents an incoming request from a channel (USSD/SMS webhook)."""
    session_id: str
    sender: str  # Phone number
    content: str  # User input
    channel_type: str  # "ussd" or "sms"
    raw_payload: dict[str, Any]  # Original webhook payload


@dataclass
class ChannelResponse:
    """Represents a response to send back through a channel."""
    content: str
    session_active: bool = False  # For USSD: CON (True) or END (False)
    metadata: dict[str, Any] | None = None


class ChannelAdapter(ABC):
    """
    Abstract base class for channel adapters (USSD, SMS, WhatsApp, etc.).
    
    Implements the Hexagonal Architecture Port pattern:
    - External channels (USSD/SMS) are adapters
    - They translate protocol-specific requests into domain actions
    - They format domain responses back into protocol-specific formats
    """
    
    @abstractmethod
    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        """
        Parse incoming webhook payload into a standardized ChannelRequest.
        
        Args:
            payload: Raw webhook payload from provider (Africa's Talking, Twilio, etc.)
            
        Returns:
            ChannelRequest with normalized data
        """
        pass
    
    @abstractmethod
    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        """
        Format a ChannelResponse into provider-specific response format.
        
        Args:
            response: Standardized response object
            
        Returns:
            Provider-specific response dict (for webhook reply)
        """
        pass
    
    @abstractmethod
    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        """
        Send an outbound message through this channel.
        
        Args:
            to: Recipient identifier (phone number, session ID, etc.)
            message: Message content
            metadata: Optional channel-specific metadata
            
        Returns:
            True if message was sent successfully
        """
        pass
    
    @abstractmethod
    def get_channel_type(self) -> str:
        """Return the channel type identifier (e.g., 'ussd', 'sms', 'whatsapp')."""
        pass


class ChannelGateway(ABC):
    """
    Abstract base class for channel gateways (API providers).
    
    Gateways handle the actual communication with external APIs:
    - Africa's Talking
    - Twilio
    - WhatsApp Business API
    - Mock implementations for testing
    """
    
    @abstractmethod
    async def send(self, to: str, message: str, **kwargs) -> dict[str, Any]:
        """
        Send a message through the gateway's API.
        
        Returns:
            API response with message ID, status, etc.
        """
        pass
    
    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> str:
        """
        Check delivery status of a sent message.
        
        Returns:
            Status string: "sent", "delivered", "failed", etc.
        """
        pass
