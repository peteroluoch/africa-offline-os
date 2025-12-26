"""
Agriculture Domain
Handles all farming and marketplace related commands.
"""
from typing import List, Dict
import logging
from aos.adapters.domains.base import BaseDomain

logger = logging.getLogger(__name__)

class AgriDomain(BaseDomain):
    """Agriculture domain logic."""
    
    @property
    def name(self) -> str:
        return "agriculture"
    
    @property
    def display_name(self) -> str:
        return "🌾 Agriculture"
    
    def get_commands(self) -> List[Dict[str, str]]:
        return [
            {"command": "harvest", "description": "Record your harvest"},
            {"command": "sell", "description": "List crops for sale"},
            {"command": "buy", "description": "Buy produce from farmers"},
            {"command": "prices", "description": "Check market prices"}
        ]
    
    def handle_command(self, chat_id: int, command: str, args: List[str]) -> bool:
        if command == "/harvest":
            self._show_harvest_menu(chat_id)
            return True
        elif command in ["/sell", "/buy", "/prices"]:
            self.adapter.send_message(chat_id, f"🚧 {command} is coming soon to the Marketplace!")
            return True
        return False
    
    def handle_callback(self, chat_id: int, callback_data: str) -> bool:
        if callback_data.startswith('harvest_'):
            crop = callback_data.replace('harvest_', '').capitalize()
            from aos.adapters.telegram_state import TelegramStateManager
            state_manager = TelegramStateManager()
            state_manager.set_state(chat_id, "harvest_quantity", {"crop": crop})
            self.adapter.send_message(chat_id, f"✅ Selected: {crop}\n\nHow many bags?")
            return True
        return False

    def _show_harvest_menu(self, chat_id: int):
        """Show crop selection keyboard."""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🌽 Maize", "callback_data": "harvest_maize"},
                    {"text": "🫘 Beans", "callback_data": "harvest_beans"}
                ],
                [
                    {"text": "☕ Coffee", "callback_data": "harvest_coffee"},
                    {"text": "🥔 Potatoes", "callback_data": "harvest_potatoes"}
                ]
            ]
        }
        self.adapter.send_message(chat_id, "🌾 <b>Select Crop to Record</b>", reply_markup=keyboard)
