from __future__ import annotations

from typing import Any

from aos.core.channels.base import ChannelAdapter, ChannelGateway, ChannelRequest, ChannelResponse
from aos.core.channels.ussd import ProtocolAT, USSDSessionManager


class USSDAdapter(ChannelAdapter):
    """
    Refactored USSD Adapter.
    Delegates menu logic to specific handlers.
    """

    def __init__(self, gateway: ChannelGateway, session_manager: USSDSessionManager | None = None):
        self.gateway = gateway
        self.session_manager = session_manager or USSDSessionManager()
        self.protocol = ProtocolAT()
        self._flow_handler = None # This will be injected by the module

    def set_flow_handler(self, handler: Any):
        self._flow_handler = handler

    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        return self.protocol.parse(payload)

    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        return self.protocol.format(response)

    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        return False

    def get_channel_type(self) -> str:
        return "ussd"

    def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        session = self.session_manager.get_or_create(request.session_id, request.sender)

        if self._flow_handler:
            response = self._flow_handler.process(session, request.content)
            if not response.session_active:
                self.session_manager.end(request.session_id)
            return response

        return ChannelResponse(content="Error: No flow handler configured.", session_active=False)
