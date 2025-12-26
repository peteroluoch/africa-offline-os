from __future__ import annotations

from typing import Any

from aos.core.channels.base import ChannelRequest, ChannelResponse


class TransportSMSHandler:
    """Command handler for the Transport vehicle."""

    def __init__(self, transport_module: Any):
        self.transport = transport_module

    def process(self, request: ChannelRequest) -> ChannelResponse:
        text = request.content.upper()

        # Example: ROUTE 46 FULL
        if text.startswith("ROUTE"):
            parts = text.split()
            if len(parts) >= 3:
                route_name = parts[1]
                status = parts[2]
                return ChannelResponse(f"✓ Route {route_name} status updated to {status}")

        return ChannelResponse("Unknown Transport command. Example: ROUTE 46 FULL")
