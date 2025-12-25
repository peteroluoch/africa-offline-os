from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from aos.adapters.channel import ChannelGateway


@dataclass
class MockSMSMessage:
    """Represents a mock SMS message."""
    message_id: str
    sender: str
    recipient: str
    content: str
    status: str = "sent"  # sent, delivered, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: datetime | None = None


class MockSMSGateway(ChannelGateway):
    """
    Mock SMS Gateway for testing without Twilio/Africa's Talking API.
    
    Simulates SMS sending and receiving:
    - Message queue (inbox/outbox)
    - Delivery status tracking
    - Webhook payload generation
    """
    
    def __init__(self, shortcode: str = "21525"):
        self.shortcode = shortcode
        self.inbox: list[MockSMSMessage] = []  # Received messages
        self.outbox: list[MockSMSMessage] = []  # Sent messages
        self.delivery_callbacks: list[dict[str, Any]] = []
    
    def receive_message(self, sender: str, content: str) -> dict[str, Any]:
        """
        Simulate receiving an SMS message.
        
        Returns:
            Webhook payload that would be sent to the application
        """
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        message = MockSMSMessage(
            message_id=message_id,
            sender=sender,
            recipient=self.shortcode,
            content=content
        )
        
        self.inbox.append(message)
        
        # Generate webhook payload (Africa's Talking format)
        payload = {
            "from": sender,
            "to": self.shortcode,
            "text": content,
            "id": message_id,
            "date": message.created_at.isoformat()
        }
        
        return payload
    
    async def send(self, to: str, message: str, **kwargs) -> dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            to: Recipient phone number
            message: Message content
            
        Returns:
            API response with message ID and status
        """
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        sms = MockSMSMessage(
            message_id=message_id,
            sender=self.shortcode,
            recipient=to,
            content=message,
            status="sent"
        )
        
        self.outbox.append(sms)
        
        # Simulate instant delivery (in real world, this would be async)
        sms.status = "delivered"
        sms.delivered_at = datetime.now(timezone.utc)
        
        return {
            "status": "success",
            "message_id": message_id,
            "recipient": to,
            "cost": "KES 1.00"  # Mock cost
        }
    
    async def get_delivery_status(self, message_id: str) -> str:
        """
        Get delivery status of a sent message.
        
        Returns:
            Status: "sent", "delivered", "failed", "unknown"
        """
        for msg in self.outbox:
            if msg.message_id == message_id:
                return msg.status
        return "unknown"
    
    def get_inbox(self) -> list[MockSMSMessage]:
        """Get all received messages."""
        return self.inbox.copy()
    
    def get_outbox(self) -> list[MockSMSMessage]:
        """Get all sent messages."""
        return self.outbox.copy()
    
    def get_message(self, message_id: str) -> MockSMSMessage | None:
        """Get a specific message by ID."""
        for msg in self.inbox + self.outbox:
            if msg.message_id == message_id:
                return msg
        return None
    
    def clear(self):
        """Clear all messages (for testing)."""
        self.inbox.clear()
        self.outbox.clear()
        self.delivery_callbacks.clear()
    
    def simulate_conversation(self, phone_number: str, messages: list[str]) -> list[MockSMSMessage]:
        """
        Simulate a conversation for testing.
        
        Args:
            phone_number: User's phone number
            messages: List of messages to send from user
            
        Returns:
            List of responses from the system
        """
        responses = []
        
        for msg in messages:
            # User sends message
            self.receive_message(phone_number, msg)
            
            # System would process and send response
            # (Actual processing happens in the adapter/router)
            # We'll collect responses in tests
        
        return responses
