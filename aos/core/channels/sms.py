from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aos.core.channels.base import ChannelRequest, ChannelResponse


@dataclass
class SMSCommand:
    command: str
    params: dict[str, Any]
    raw_text: str


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
