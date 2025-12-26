from __future__ import annotations

from aos.core.channels.base import ChannelRequest, ChannelResponse


class AgriSMSHandler:
    """Command handler for the Agri vehicle."""

    def process(self, request: ChannelRequest) -> ChannelResponse:
        text = request.content.upper()

        if "HARVEST" in text:
            # Simplified parsing for now
            return ChannelResponse("✓ SMS Harvest recorded. Ref: H-2025-001")

        return ChannelResponse("Unknown Agri command. Use HARVEST [CROP] [QTY] [GRADE]")
