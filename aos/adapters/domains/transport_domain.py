"""
Transport Domain
Handles all mobility and logistics related commands.
"""
from typing import List, Dict
import logging
from aos.adapters.domains.base import BaseDomain

logger = logging.getLogger(__name__)

class TransportDomain(BaseDomain):
    """Transport domain logic."""
    
    @property
    def name(self) -> str:
        return "transport"
    
    @property
    def display_name(self) -> str:
        return "🚌 Transport"
    
    def get_commands(self) -> List[Dict[str, str]]:
        return [
            {"command": "routes", "description": "View available routes"},
            {"command": "book", "description": "Book a transport seat"},
            {"command": "schedule", "description": "View vehicle schedules"}
        ]
    
    def handle_command(self, chat_id: int, command: str, args: List[str]) -> bool:
        if command == "/routes":
            self._show_routes(chat_id)
            return True
        elif command == "/book":
            self._show_booking_menu(chat_id)
            return True
        elif command == "/schedule":
            self.adapter.send_message(chat_id, "🚧 /schedule is coming soon!")
            return True
        return False
    
    def handle_callback(self, chat_id: int, callback_data: str) -> bool:
        if callback_data.startswith('book_route_'):
            route_id = callback_data.replace('book_route_', '')
            from aos.adapters.telegram_state import TelegramStateManager
            state_manager = TelegramStateManager()
            
            route_names = {
                "1": "Nairobi → Nakuru",
                "2": "Nairobi → Kisumu",
                "3": "Nakuru → Eldoret"
            }
            route_name = route_names.get(route_id, "Unknown")
            state_manager.set_state(chat_id, "booking_passengers", {"route": route_name, "route_id": route_id})
            self.adapter.send_message(chat_id, f"✅ Selected Route: {route_name}\n\nHow many passengers?")
            return True
        return False

    def _show_routes(self, chat_id: int):
        """Show available routes."""
        routes_text = (
            "🚌 <b>Available Routes</b>\n\n"
            "1. Nairobi → Nakuru (Departs: 08:00)\n"
            "2. Nairobi → Kisumu (Departs: 09:30)\n"
            "3. Nakuru → Eldoret (Departs: 14:00)\n\n"
            "Use /book to reserve a seat."
        )
        self.adapter.send_message(chat_id, routes_text)

    def _show_booking_menu(self, chat_id: int):
        """Show route selection for booking."""
        keyboard = {
            "inline_keyboard": [
                [{"text": "Nairobi → Nakuru", "callback_data": "book_route_1"}],
                [{"text": "Nairobi → Kisumu", "callback_data": "book_route_2"}],
                [{"text": "Nakuru → Eldoret", "callback_data": "book_route_3"}]
            ]
        }
        self.adapter.send_message(chat_id, "🚌 <b>Select Route to Book</b>", reply_markup=keyboard)
