from __future__ import annotations
from typing import Any
from aos.core.channels.base import ChannelResponse
from aos.core.channels.ussd import USSDSession


class TransportUSSDHandler:
    """Menu flow handler for the Transport vehicle."""
    
    def __init__(self, transport_module: Any):
        self.transport = transport_module

    def process(self, session: USSDSession, user_input: str) -> ChannelResponse:
        state = session.state
        user_input = user_input.strip()

        if state == "START":
            if not user_input:
                return ChannelResponse("[A-OS Transport]\n1. Check Route\n2. Report Status (Driver)", True)
            
            if user_input == "1":
                session.update("SELECT_ROUTE")
                routes = self.transport.list_routes()
                menu = "Select Route:\n"
                for i, r in enumerate(routes, 1):
                    menu += f"{i}. {r['name']}\n"
                session.data["routes_map"] = {str(i): r['id'] for i, r in enumerate(routes, 1)}
                return ChannelResponse(menu, True)
            
            if user_input == "2":
                session.update("DRIVER_PLATE")
                return ChannelResponse("Enter Vehicle Plate:", True)

        if state == "SELECT_ROUTE":
            r_map = session.data.get("routes_map", {})
            if user_input in r_map:
                route_id = r_map[user_input]
                status = self.transport.get_route_status(route_id)
                num_v = len(status['vehicles'])
                msg = f"{status['route_name']}\n"
                msg += f"Available: {num_v} vehicles\n"
                if num_v > 0:
                    msg += f"Next: {status['vehicles'][0]['plate']}"
                return ChannelResponse(msg, False)
            return ChannelResponse("Invalid route.", False)

        if state == "DRIVER_PLATE":
            if user_input:
                session.update("DRIVER_STATUS", plate=user_input)
                return ChannelResponse("Status:\n1. Available\n2. Full\n3. Off Duty", True)
            return ChannelResponse("Enter plate.", True)

        if state == "DRIVER_STATUS":
            status_map = {"1": "AVAILABLE", "2": "FULL", "3": "OFF_DUTY"}
            if user_input in status_map:
                status = status_map[user_input]
                plate = session.data.get("plate")
                # TODO: Actually update DB
                return ChannelResponse(f"✓ Status updated for {plate}: {status}", False)
            return ChannelResponse("Invalid status.", False)

        return ChannelResponse("Transport Error.", False)
