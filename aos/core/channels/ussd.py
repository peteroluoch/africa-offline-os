from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aos.core.channels.base import ChannelRequest, ChannelResponse


@dataclass
class USSDSession:
    """Represents an active USSD session."""
    session_id: str
    phone_number: str
    state: str = "START"
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update(self, state: str, **kwargs):
        self.state = state
        self.data.update(kwargs)
        self.updated_at = datetime.now(UTC)


class USSDSessionManager:
    """Manages USSD session states across requests."""

    def __init__(self):
        self._sessions: dict[str, USSDSession] = {}

    def get_or_create(self, session_id: str, phone_number: str) -> USSDSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = USSDSession(session_id, phone_number)
        return self._sessions[session_id]

    def end(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def cleanup(self, max_age_seconds: int = 300):
        now = datetime.now(UTC)
        expired = [
            sid for sid, sess in self._sessions.items()
            if (now - sess.updated_at).total_seconds() > max_age_seconds
        ]
        for sid in expired:
            del self._sessions[sid]


class ProtocolAT:
    """Africa's Talking USSD Protocol Handler."""

    @staticmethod
    def parse(payload: dict[str, Any]) -> ChannelRequest:
        sid = payload.get("sessionId", "")
        phone = payload.get("phoneNumber", "")
        text = payload.get("text", "")

        inputs = text.split("*") if text else []
        latest = inputs[-1] if inputs else ""

        return ChannelRequest(
            session_id=sid,
            sender=phone,
            content=latest,
            channel_type="ussd",
            raw_payload=payload
        )

    @staticmethod
    def format(response: ChannelResponse) -> dict[str, Any]:
        prefix = "CON" if response.session_active else "END"
        return {"text": f"{prefix} {response.content}"}
