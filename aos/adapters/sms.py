from __future__ import annotations
from typing import Any
from aos.core.channels.base import ChannelAdapter, ChannelRequest, ChannelResponse, ChannelGateway
from aos.core.channels.sms import SMSProtocolAT


class SMSAdapter(ChannelAdapter):
    """
    Refactored SMS Adapter.
    Delegates command processing to specific handlers.
    """
    
    def __init__(self, gateway: ChannelGateway):
        self.gateway = gateway
        self.protocol = SMSProtocolAT()
        self._command_handler = None
        
    def set_command_handler(self, handler: Any):
        self._command_handler = handler

    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        return self.protocol.parse(payload)
    
    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        return self.protocol.format(response)
    
    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        try:
            await self.gateway.send(to, message)
            return True
        except:
            return False
    
    def get_channel_type(self) -> str:
        return "sms"
    
    def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        if self._command_handler:
            return self._command_handler.process(request)
            
        return ChannelResponse(content="Error: No command handler configured.", session_active=False)
