from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from aos.adapters.channel import ChannelGateway


@dataclass
class MockUSSDSession:
    """Represents a mock USSD session for testing."""
    session_id: str
    phone_number: str
    service_code: str
    inputs: list[str] = field(default_factory=list)
    responses: list[str] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MockUSSDGateway(ChannelGateway):
    """
    Mock USSD Gateway for testing without Africa's Talking API.
    
    Simulates the behavior of Africa's Talking USSD API:
    - Tracks sessions
    - Generates webhook payloads
    - Validates responses
    """
    
    def __init__(self, service_code: str = "*384*2025#"):
        self.service_code = service_code
        self.sessions: dict[str, MockUSSDSession] = {}
        self.message_log: list[dict[str, Any]] = []
    
    def start_session(self, phone_number: str) -> str:
        """
        Start a new USSD session.
        
        Returns:
            session_id
        """
        session_id = f"ATUid_{uuid.uuid4().hex[:16]}"
        self.sessions[session_id] = MockUSSDSession(
            session_id=session_id,
            phone_number=phone_number,
            service_code=self.service_code
        )
        return session_id
    
    def send_input(self, session_id: str, user_input: str) -> dict[str, Any]:
        """
        Simulate user sending input in a USSD session.
        
        Returns:
            Webhook payload that would be sent to the application
        """
        session = self.sessions.get(session_id)
        if not session or not session.active:
            raise ValueError(f"Session {session_id} not found or inactive")
        
        session.inputs.append(user_input)
        
        # Build the "text" field (input history)
        text = "*".join(session.inputs)
        
        # Generate webhook payload (Africa's Talking format)
        payload = {
            "sessionId": session_id,
            "phoneNumber": session.phone_number,
            "text": text,
            "serviceCode": self.service_code
        }
        
        return payload
    
    def receive_response(self, session_id: str, response_text: str):
        """
        Receive and process a response from the application.
        
        Args:
            session_id: Session ID
            response_text: Response text (e.g., "CON Select crop:\n1. Maize")
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.responses.append(response_text)
        
        # Check if session should end
        if response_text.startswith("END"):
            session.active = False
        
        # Log the interaction
        self.message_log.append({
            "session_id": session_id,
            "phone_number": session.phone_number,
            "response": response_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def get_session(self, session_id: str) -> MockUSSDSession | None:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def get_last_response(self, session_id: str) -> str | None:
        """Get the last response for a session."""
        session = self.sessions.get(session_id)
        if session and session.responses:
            return session.responses[-1]
        return None
    
    async def send(self, to: str, message: str, **kwargs) -> dict[str, Any]:
        """USSD doesn't support outbound messages."""
        return {"status": "error", "message": "USSD does not support outbound messages"}
    
    async def get_delivery_status(self, message_id: str) -> str:
        """USSD doesn't have delivery status."""
        return "not_applicable"
    
    def simulate_conversation(self, phone_number: str, inputs: list[str]) -> list[str]:
        """
        Simulate a full USSD conversation for testing.
        
        Args:
            phone_number: User's phone number
            inputs: List of user inputs
            
        Returns:
            List of responses from the application
        """
        session_id = self.start_session(phone_number)
        responses = []
        
        # First request (empty input to show menu)
        payload = self.send_input(session_id, "")
        # Application would process this and return a response
        # (This is just the gateway - actual processing happens in the adapter)
        
        for user_input in inputs:
            payload = self.send_input(session_id, user_input)
            # Application processes and returns response
            # We'll collect responses in tests
        
        return responses
