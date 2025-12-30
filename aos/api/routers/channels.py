from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from aos.adapters.africas_talking import SMSAdapter, USSDAdapter
from aos.adapters.mocks.mock_sms_gateway import MockSMSGateway
from aos.adapters.mocks.mock_ussd_gateway import MockUSSDGateway
from aos.api.state import transport_state
from aos.core.channels.base import ChannelResponse
from aos.core.security.auth import get_current_operator
from aos.modules.agri_sms import AgriSMSHandler
from aos.modules.agri_ussd import AgriUSSDHandler
from aos.modules.community.ussd_adapter import CommunityUSSDHandler
from aos.modules.transport.sms_adapter import TransportSMSHandler
from aos.modules.transport.ussd_adapter import TransportUSSDHandler

router = APIRouter(prefix="/channels", tags=["channels"])

# Initialize mock gateways
_ussd_gateway = MockUSSDGateway()
_sms_gateway = MockSMSGateway()

# Initialize adapters
_ussd_adapter = USSDAdapter(_ussd_gateway)
_sms_adapter = SMSAdapter(_sms_gateway)

# Multi-Vehicle Router (Internal Mock)
class MultiVehicleUSSDHandler:
    def __init__(self):
        from aos.api.state import agri_state, community_state
        self.agri = AgriUSSDHandler(agri_state.module)
        self.community = CommunityUSSDHandler(community_state.module)
        # Note: transport_state.module might be None during router init,
        # so we'll init handler inside process if needed or use lazy loading
        self.transport = None

    async def process(self, session, user_input):
        from aos.api.state import agri_state, transport_state, community_state
        
        # Ensure handlers are refreshed with modules if they were None at init
        if not self.agri.agri and agri_state.module:
            self.agri.agri = agri_state.module
            
        if not self.community.community and community_state.module:
            self.community.community = community_state.module

        if not self.transport and transport_state.module:
            self.transport = TransportUSSDHandler(transport_state.module)

        # Logic: If session already has a vehicle, use it
        vehicle = session.data.get("vehicle")

        if not vehicle:
            if not user_input:
                return ChannelResponse("[A-OS Central]\n1. Agri-Lighthouse\n2. Transport-Mobile\n3. Community-Pulse", True)
            if user_input == "1":
                session.data["vehicle"] = "agri"
                session.state = "START"
                return await self.agri.process(session, "")
            if user_input == "2":
                session.data["vehicle"] = "transport"
                session.state = "START"
                if self.transport:
                    return await self.transport.process(session, "")
                return ChannelResponse("Transport module starting...", False)
            if user_input == "3":
                session.data["vehicle"] = "community"
                session.state = "START"
                return await self.community.process(session, "")
            return ChannelResponse("Invalid selection.", False)

        if vehicle == "agri":
            return await self.agri.process(session, user_input)
        if vehicle == "transport":
            if self.transport:
                return await self.transport.process(session, user_input)
        if vehicle == "community":
            return await self.community.process(session, user_input)

        return ChannelResponse("Error: Vehicle not found.", False)

from aos.api.state import agri_state
_ussd_adapter.set_flow_handler(MultiVehicleUSSDHandler())
_sms_adapter.set_command_handler(AgriSMSHandler(agri_state.module))


@router.post("/ussd", response_class=PlainTextResponse)
async def ussd_webhook(request: Request):
    """
    USSD webhook endpoint for Africa's Talking.
    
    Expected payload:
    {
        "sessionId": "ATUid_...",
        "phoneNumber": "+254712345678",
        "text": "1*2*15",
        "serviceCode": "*384*2025#"
    }
    
    Response format:
    "CON Select crop:\n1. Maize\n2. Beans"
    or
    "END Harvest recorded!"
    """
    try:
        # Parse incoming webhook
        payload = await request.json()

        # Parse request using adapter
        channel_request = _ussd_adapter.parse_request(payload)

        # Handle the request (state machine processing)
        channel_response = await _ussd_adapter.handle_request(channel_request)

        # Format response for Africa's Talking
        formatted_response = _ussd_adapter.format_response(channel_response)

        # Return plain text response
        return formatted_response["text"]

    except Exception as e:
        print(f"[USSD Webhook] Error: {e}")
        return "END An error occurred. Please try again."


@router.post("/sms", response_class=JSONResponse)
async def sms_webhook(request: Request):
    """
    SMS webhook endpoint for Africa's Talking / Twilio.
    
    Expected payload (Africa's Talking):
    {
        "from": "+254712345678",
        "to": "21525",
        "text": "HARVEST MAIZE 15 A",
        "id": "msg_id_123",
        "date": "2025-12-25 12:00:00"
    }
    
    Response:
    {
        "message": "✓ Harvest recorded\n15 bags Grade A Maize\nRef: H-2025-001"
    }
    """
    try:
        # Parse incoming webhook
        payload = await request.json()

        # Parse request using adapter
        channel_request = _sms_adapter.parse_request(payload)

        # Handle the request (command parsing and processing)
        channel_response = await _sms_adapter.handle_request(channel_request)

        # Send response SMS
        await _sms_adapter.send_message(
            to=channel_request.sender,
            message=channel_response.content
        )

        # Return success (webhook acknowledgment)
        return {"status": "success", "message": "SMS processed"}

    except Exception as e:
        print(f"[SMS Webhook] Error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint for receiving bot messages.
    
    Uses the full TelegramAdapter for interactive bot functionality.
    Supports registration, domain selection, and domain-specific commands.
    """
    import os
    import hmac
    
    try:
        # Verify webhook secret token
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        
        if not secret_token or not expected_secret:
            print("[Telegram Webhook] Missing secret token")
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": "Unauthorized"}
            )
        
        if not hmac.compare_digest(secret_token, expected_secret):
            print("[Telegram Webhook] Invalid secret token")
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "Forbidden"}
            )
        
        # Parse webhook payload
        update = await request.json()
        print(f"[Telegram Webhook] Received update: {update}")
        
        # Initialize Telegram Adapter
        from aos.adapters.telegram import TelegramAdapter
        from aos.api.state import core_state, agri_state, transport_state, community_state
        
        telegram_adapter = TelegramAdapter(
            event_bus=core_state.event_dispatcher,
            agri_module=agri_state.module,
            transport_module=transport_state.module,
            community_module=community_state.module
        )
        
        # Handle message or callback query
        if "message" in update:
            await telegram_adapter.handle_message(update["message"])
        elif "callback_query" in update:
            callback = update["callback_query"]
            await telegram_adapter.handle_callback(
                user_id=callback["from"]["id"],
                chat_id=callback["message"]["chat"]["id"],
                callback_data=callback["data"]
            )
        
        # Return success (Telegram requires 200 OK)
        return {"ok": True}
    
    except Exception as e:
        print(f"[Telegram Webhook] Error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


# Debug endpoints (protected)

@router.get("/ussd/sessions")
async def get_ussd_sessions(current_user: dict = Depends(get_current_operator)):
    """
    Debug endpoint: View active USSD sessions.
    
    Protected - requires authentication.
    """
    sessions = []
    for session_id, session in _ussd_adapter.session_manager._sessions.items():
        sessions.append({
            "session_id": session.session_id,
            "phone_number": session.phone_number,
            "state": session.state,
            "data": session.data,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        })

    return {
        "total": len(sessions),
        "sessions": sessions
    }


@router.get("/sms/messages")
async def get_sms_messages(current_user: dict = Depends(get_current_operator)):
    """
    Debug endpoint: View SMS message queue.
    
    Protected - requires authentication.
    """
    inbox = _sms_gateway.get_inbox()
    outbox = _sms_gateway.get_outbox()

    return {
        "inbox": [
            {
                "message_id": msg.message_id,
                "sender": msg.sender,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in inbox
        ],
        "outbox": [
            {
                "message_id": msg.message_id,
                "recipient": msg.recipient,
                "content": msg.content,
                "status": msg.status,
                "created_at": msg.created_at.isoformat()
            }
            for msg in outbox
        ]
    }


@router.post("/ussd/test")
async def test_ussd(
    phone_number: str,
    inputs: list[str],
    current_user: dict = Depends(get_current_operator)
):
    """
    Debug endpoint: Test USSD flow without external API.
    
    Example:
    POST /channels/ussd/test
    {
        "phone_number": "+254712345678",
        "inputs": ["1", "1", "15", "1"]
    }
    """
    session_id = _ussd_gateway.start_session(phone_number)
    responses = []

    # Initial request (empty input)
    payload = _ussd_gateway.send_input(session_id, "")
    channel_request = _ussd_adapter.parse_request(payload)
    channel_response = await _ussd_adapter.handle_request(channel_request)
    formatted = _ussd_adapter.format_response(channel_response)
    responses.append(formatted["text"])
    _ussd_gateway.receive_response(session_id, formatted["text"])

    # Process each input
    for user_input in inputs:
        payload = _ussd_gateway.send_input(session_id, user_input)
        channel_request = _ussd_adapter.parse_request(payload)
        channel_response = await _ussd_adapter.handle_request(channel_request)
        formatted = _ussd_adapter.format_response(channel_response)
        responses.append(formatted["text"])
        _ussd_gateway.receive_response(session_id, formatted["text"])

    return {
        "session_id": session_id,
        "phone_number": phone_number,
        "inputs": inputs,
        "responses": responses
    }


@router.post("/sms/test")
async def test_sms(
    phone_number: str,
    message: str,
    current_user: dict = Depends(get_current_operator)
):
    """
    Debug endpoint: Test SMS command parsing without external API.
    
    Example:
    POST /channels/sms/test
    {
        "phone_number": "+254712345678",
        "message": "HARVEST MAIZE 15 A"
    }
    """
    # Simulate receiving SMS
    payload = _sms_gateway.receive_message(phone_number, message)

    # Process with adapter
    channel_request = _sms_adapter.parse_request(payload)
    channel_response = await _sms_adapter.handle_request(channel_request)

    # Send response
    await _sms_adapter.send_message(phone_number, channel_response.content)

    return {
        "phone_number": phone_number,
        "incoming_message": message,
        "response": channel_response.content,
        "outbox": [
            {
                "recipient": msg.recipient,
                "content": msg.content,
                "status": msg.status
            }
            for msg in _sms_gateway.get_outbox()
        ]
    }
