from __future__ import annotations
import re
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timezone
from aos.adapters.channel import ChannelAdapter, ChannelRequest, ChannelResponse, ChannelGateway


@dataclass
class SMSCommand:
    """Represents a parsed SMS command."""
    command: str  # e.g., "HARVEST", "PRICE", "BUYER"
    crop: str | None = None
    quantity: float | None = None
    quality: str | None = None
    raw_text: str = ""


class SMSCommandParser:
    """
    Parses SMS text commands into structured data.
    
    Supported formats:
    - HARVEST MAIZE 15 A
    - HARVEST maize 15 bags grade A
    - I harvested 15 bags of maize, grade A
    """
    
    # Crop name mappings
    CROP_MAPPINGS = {
        "maize": "maize-01",
        "corn": "maize-01",
        "beans": "beans-01",
        "sorghum": "sorghum-01",
        "millet": "sorghum-01"
    }
    
    # Quality grade mappings
    QUALITY_MAPPINGS = {
        "grade a": "A",
        "grade b": "B",
        "grade c": "C",
        " a": "A",  # Space before to avoid matching "maize"
        " b": "B",
        " c": "C"
    }
    
    def parse(self, text: str) -> SMSCommand:
        """
        Parse SMS text into a structured command.
        
        Args:
            text: Raw SMS text
            
        Returns:
            SMSCommand with extracted data
        """
        text = text.strip().lower()
        
        # Detect command type
        if "harvest" in text:
            return self._parse_harvest(text)
        elif "price" in text:
            return SMSCommand(command="PRICE", raw_text=text)
        elif "buyer" in text:
            return SMSCommand(command="BUYER", raw_text=text)
        else:
            return SMSCommand(command="UNKNOWN", raw_text=text)
    
    def _parse_harvest(self, text: str) -> SMSCommand:
        """Parse a harvest command."""
        command = SMSCommand(command="HARVEST", raw_text=text)
        
        # Extract crop
        for crop_name, crop_id in self.CROP_MAPPINGS.items():
            if crop_name in text:
                command.crop = crop_id
                break
        
        # Extract quantity (look for numbers)
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            try:
                command.quantity = float(numbers[0])
            except ValueError:
                pass
        
        # Extract quality grade (check longer patterns first)
        for quality_text, quality_code in sorted(self.QUALITY_MAPPINGS.items(), key=lambda x: len(x[0]), reverse=True):
            if quality_text in text:
                command.quality = quality_code
                break
        
        return command
    
    def validate(self, command: SMSCommand) -> tuple[bool, str]:
        """
        Validate a parsed command.
        
        Returns:
            (is_valid, error_message)
        """
        if command.command == "HARVEST":
            if not command.crop:
                return False, "Crop not specified. Example: HARVEST MAIZE 15 A"
            if not command.quantity:
                return False, "Quantity not specified. Example: HARVEST MAIZE 15 A"
            if not command.quality:
                return False, "Quality grade not specified. Example: HARVEST MAIZE 15 A"
            if command.quantity <= 0:
                return False, "Quantity must be greater than 0"
        
        return True, ""


class SMSAdapter(ChannelAdapter):
    """
    SMS Channel Adapter for the Agri-Lighthouse.
    
    Handles command-based interactions via SMS.
    """
    
    def __init__(self, gateway: ChannelGateway):
        self.gateway = gateway
        self.parser = SMSCommandParser()
    
    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        """
        Parse SMS webhook payload.
        
        Expected payload format (Africa's Talking):
        {
            "from": "+254712345678",
            "to": "21525",
            "text": "HARVEST MAIZE 15 A",
            "id": "msg_id_123",
            "date": "2025-12-25 12:00:00"
        }
        
        Or Twilio format:
        {
            "From": "+254712345678",
            "To": "21525",
            "Body": "HARVEST MAIZE 15 A",
            "MessageSid": "SM..."
        }
        """
        # Normalize different provider formats
        sender = payload.get("from") or payload.get("From", "")
        text = payload.get("text") or payload.get("Body", "")
        message_id = payload.get("id") or payload.get("MessageSid", "")
        
        return ChannelRequest(
            session_id=message_id,
            sender=sender,
            content=text,
            channel_type="sms",
            raw_payload=payload
        )
    
    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        """
        Format response for SMS webhook reply.
        
        Returns:
        {
            "message": "✓ Harvest recorded\n15 bags Grade A Maize\nRef: H-2025-001"
        }
        """
        return {
            "message": response.content
        }
    
    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        """Send an SMS message via the gateway."""
        try:
            result = await self.gateway.send(to, message)
            return result.get("status") == "success"
        except Exception as e:
            print(f"[SMSAdapter] Failed to send message: {e}")
            return False
    
    def get_channel_type(self) -> str:
        return "sms"
    
    def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        """
        Main request handler - parses command and returns response.
        """
        # Parse the SMS text
        command = self.parser.parse(request.content)
        
        # Validate the command
        is_valid, error_message = self.parser.validate(command)
        
        if not is_valid:
            return ChannelResponse(
                content=f"❌ Error: {error_message}",
                session_active=False
            )
        
        # Handle different command types
        if command.command == "HARVEST":
            return self._handle_harvest(command, request.sender)
        elif command.command == "PRICE":
            return ChannelResponse(
                content="Price checking feature coming soon!",
                session_active=False
            )
        elif command.command == "BUYER":
            return ChannelResponse(
                content="Buyer matching feature coming soon!",
                session_active=False
            )
        else:
            return ChannelResponse(
                content="Unknown command. Send HELP for assistance.",
                session_active=False
            )
    
    def _handle_harvest(self, command: SMSCommand, farmer_phone: str) -> ChannelResponse:
        """Handle harvest recording command."""
        # TODO: Call AgriModule.record_harvest() here
        # For now, just confirm
        
        crop_name = command.crop or "Unknown"
        quantity = command.quantity or 0
        quality = command.quality or ""
        
        return ChannelResponse(
            content=f"✓ Harvest recorded\n{quantity} bags Grade {quality} {crop_name}\nRef: H-2025-001\nThank you!",
            session_active=False
        )
