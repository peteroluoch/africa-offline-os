from __future__ import annotations
from typing import Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from aos.adapters.channel import ChannelAdapter, ChannelRequest, ChannelResponse, ChannelGateway


class USSDSessionState(str, Enum):
    """USSD conversation states for the Agri-Lighthouse flow."""
    MAIN_MENU = "main_menu"
    SELECT_CROP = "select_crop"
    ENTER_QUANTITY = "enter_quantity"
    ENTER_QUALITY = "enter_quality"
    CONFIRM = "confirm"
    ERROR = "error"


@dataclass
class USSDSession:
    """Represents an active USSD session."""
    session_id: str
    phone_number: str
    state: USSDSessionState
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_state(self, new_state: USSDSessionState, user_input: str | None = None):
        """Update session state and store user input."""
        self.state = new_state
        self.updated_at = datetime.now(timezone.utc)
        if user_input:
            self.data[new_state.value] = user_input


class USSDSessionManager:
    """
    Manages USSD session state across multiple requests.
    
    USSD is stateful - each user interaction is a separate HTTP request,
    but we need to maintain conversation context.
    """
    
    def __init__(self):
        self._sessions: dict[str, USSDSession] = {}
    
    def get_or_create_session(self, session_id: str, phone_number: str) -> USSDSession:
        """Get existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = USSDSession(
                session_id=session_id,
                phone_number=phone_number,
                state=USSDSessionState.MAIN_MENU
            )
        return self._sessions[session_id]
    
    def get_session(self, session_id: str) -> USSDSession | None:
        """Get an existing session."""
        return self._sessions.get(session_id)
    
    def end_session(self, session_id: str):
        """End and remove a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def cleanup_old_sessions(self, max_age_seconds: int = 300):
        """Remove sessions older than max_age_seconds (default 5 minutes)."""
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, session in self._sessions.items()
            if (now - session.updated_at).total_seconds() > max_age_seconds
        ]
        for sid in expired:
            del self._sessions[sid]


class USSDAdapter(ChannelAdapter):
    """
    USSD Channel Adapter for the Agri-Lighthouse.
    
    Handles the conversational flow for harvest recording via USSD.
    """
    
    def __init__(self, gateway: ChannelGateway, session_manager: USSDSessionManager | None = None):
        self.gateway = gateway
        self.session_manager = session_manager or USSDSessionManager()
        
        # Crop mapping (ID -> Name)
        self.crops = {
            "1": "maize-01",
            "2": "beans-01",
            "3": "sorghum-01"
        }
        
        # Quality mapping
        self.quality_grades = {
            "1": "A",
            "2": "B",
            "3": "C"
        }
    
    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        """
        Parse Africa's Talking USSD webhook payload.
        
        Expected payload format:
        {
            "sessionId": "ATUid_...",
            "phoneNumber": "+254712345678",
            "text": "1*2*15",  # User's input history
            "serviceCode": "*384*2025#"
        }
        """
        session_id = payload.get("sessionId", "")
        phone_number = payload.get("phoneNumber", "")
        text = payload.get("text", "")
        
        # Extract latest input (after last *)
        inputs = text.split("*") if text else []
        latest_input = inputs[-1] if inputs else ""
        
        return ChannelRequest(
            session_id=session_id,
            sender=phone_number,
            content=latest_input,
            channel_type="ussd",
            raw_payload=payload
        )
    
    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        """
        Format response for Africa's Talking USSD.
        
        Returns:
        {
            "sessionId": "...",
            "text": "CON Select crop:\n1. Maize\n2. Beans" 
        }
        
        CON = Continue session
        END = End session
        """
        prefix = "CON" if response.session_active else "END"
        return {
            "text": f"{prefix} {response.content}"
        }
    
    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        """USSD doesn't support outbound messages - only responses to user-initiated sessions."""
        return False
    
    def get_channel_type(self) -> str:
        return "ussd"
    
    def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        """
        Main request handler - processes user input and returns appropriate response.
        """
        session = self.session_manager.get_or_create_session(
            request.session_id,
            request.sender
        )
        
        user_input = request.content.strip()
        
        # State machine
        if session.state == USSDSessionState.MAIN_MENU:
            return self._handle_main_menu(session, user_input)
        elif session.state == USSDSessionState.SELECT_CROP:
            return self._handle_select_crop(session, user_input)
        elif session.state == USSDSessionState.ENTER_QUANTITY:
            return self._handle_enter_quantity(session, user_input)
        elif session.state == USSDSessionState.ENTER_QUALITY:
            return self._handle_enter_quality(session, user_input)
        else:
            return ChannelResponse(
                content="Error: Invalid session state",
                session_active=False
            )
    
    def _handle_main_menu(self, session: USSDSession, user_input: str) -> ChannelResponse:
        """Display main menu or process selection."""
        if not user_input:
            # First request - show menu
            return ChannelResponse(
                content="[A-OS Agri]\n1. Record Harvest\n2. Check Prices\n3. Find Buyer",
                session_active=True
            )
        
        if user_input == "1":
            session.update_state(USSDSessionState.SELECT_CROP)
            return ChannelResponse(
                content="Select Crop:\n1. Maize\n2. Beans\n3. Sorghum",
                session_active=True
            )
        else:
            return ChannelResponse(
                content="Feature coming soon!\nThank you for using A-OS Agri.",
                session_active=False
            )
    
    def _handle_select_crop(self, session: USSDSession, user_input: str) -> ChannelResponse:
        """Handle crop selection."""
        if user_input in self.crops:
            session.data["crop_id"] = self.crops[user_input]
            session.update_state(USSDSessionState.ENTER_QUANTITY)
            return ChannelResponse(
                content="Enter quantity (bags):",
                session_active=True
            )
        else:
            return ChannelResponse(
                content="Invalid selection.\nPlease try again.",
                session_active=False
            )
    
    def _handle_enter_quantity(self, session: USSDSession, user_input: str) -> ChannelResponse:
        """Handle quantity input."""
        try:
            quantity = float(user_input)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            session.data["quantity"] = quantity
            session.update_state(USSDSessionState.ENTER_QUALITY)
            return ChannelResponse(
                content="Quality Grade:\n1. Grade A\n2. Grade B\n3. Grade C",
                session_active=True
            )
        except ValueError:
            return ChannelResponse(
                content="Invalid quantity.\nPlease enter a number.",
                session_active=False
            )
    
    def _handle_enter_quality(self, session: USSDSession, user_input: str) -> ChannelResponse:
        """Handle quality grade selection and finalize harvest."""
        if user_input in self.quality_grades:
            session.data["quality_grade"] = self.quality_grades[user_input]
            session.update_state(USSDSessionState.CONFIRM)
            
            # TODO: Call AgriModule.record_harvest() here
            # For now, just confirm
            
            crop_name = session.data.get("crop_id", "Unknown")
            quantity = session.data.get("quantity", 0)
            quality = session.data.get("quality_grade", "")
            
            self.session_manager.end_session(session.session_id)
            
            return ChannelResponse(
                content=f"✓ Harvest recorded!\n{quantity} bags Grade {quality} {crop_name}\nRef: H-2025-001",
                session_active=False
            )
        else:
            return ChannelResponse(
                content="Invalid selection.\nPlease try again.",
                session_active=False
            )
