from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aos.core.channels.base import ChannelRequest, ChannelResponse


@dataclass
class SMSCommand:
    command: str
    params: dict[str, Any]
    raw_text: str

