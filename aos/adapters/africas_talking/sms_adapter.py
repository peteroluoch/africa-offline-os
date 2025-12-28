from __future__ import annotations

import asyncio
import time
from typing import Any

from aos.core.channels.base import ChannelAdapter, ChannelGateway, ChannelRequest, ChannelResponse
from aos.core.security.rate_limiter import TokenBucketLimiter


class SMSProtocolAT:
    """Africa's Talking SMS Protocol Handler."""

    @staticmethod
    def parse(payload: dict[str, Any]) -> ChannelRequest:
        sender = payload.get("from", "")
        text = payload.get("text", "")
        msg_id = payload.get("id", "")

        return ChannelRequest(
            session_id=msg_id,
            sender=sender,
            content=text,
            channel_type="sms",
            raw_payload=payload
        )

    @staticmethod
    def format(response: ChannelResponse) -> dict[str, Any]:
        return {"message": response.content}


class SMSAdapter(ChannelAdapter):
    """
    Refactored SMS Adapter.
    Delegates command processing to specific handlers.
    """

    def __init__(self, gateway: ChannelGateway, rate_limiter: TokenBucketLimiter | None = None):
        self.gateway = gateway
        self.protocol = SMSProtocolAT()
        self.rate_limiter = rate_limiter or TokenBucketLimiter(capacity=5, fill_rate=0.1)  # 5 msg burst, 1 every 10s
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

    async def handle_request(self, request: ChannelRequest) -> ChannelResponse:
        # Check rate limit
        if self.rate_limiter:
            status = self.rate_limiter.check(request.sender)
            if not status.allowed:
                return ChannelResponse(
                    content=f"Error: Rate limit exceeded. Try again in {int(status.reset_at - time.time())}s",
                    session_active=False
                )

        if self._command_handler:
            # Support both sync and async command handlers
            if asyncio.iscoroutinefunction(self._command_handler.process):
                return await self._command_handler.process(request)
            else:
                return self._command_handler.process(request)

        return ChannelResponse(content="Error: No command handler configured.", session_active=False)
