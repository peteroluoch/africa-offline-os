"""
Telegram Bot Adapter for A-OS
Handles Telegram bot interactions for Agri and Transport modules.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule

logger = logging.getLogger(__name__)

class TelegramAdapter:
    """
    Telegram Bot Adapter for A-OS.
    Handles incoming messages and routes to appropriate module handlers.
    """

    def __init__(
        self,
        event_bus: EventDispatcher,
        agri_module: AgriModule | None = None,
        transport_module: TransportModule | None = None
    ):
        self.event_bus = event_bus
        self.agri_module = agri_module
        self.transport_module = transport_module
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')

        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - Telegram bot disabled")

    @staticmethod
    def get_bot_token() -> str:
        """Get Telegram bot token from environment."""
        return os.getenv('TELEGRAM_BOT_TOKEN', '')

    def send_message(self, chat_id: str, text: str, reply_markup: dict | None = None, parse_mode: str = "HTML") -> bool:
        """
        Send message to Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            reply_markup: Optional inline keyboard
            parse_mode: Message parse mode (HTML or Markdown)
        
        Returns:
            bool: True if successful
        """
        if not self.bot_token:
            logger.error("Cannot send message - bot token not configured")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        if reply_markup:
            payload['reply_markup'] = reply_markup

        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get('ok'):
                return True
            else:
                error = result.get('description', 'Unknown error')
                logger.error(f"Telegram API error: {error}")
                return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    @staticmethod
    def send_typing_action(chat_id: str) -> bool:
        """Send typing indicator to chat."""
        token = TelegramAdapter.get_bot_token()
        if not token:
            return False

        url = f"https://api.telegram.org/bot{token}/sendChatAction"
        payload = {
            'chat_id': chat_id,
            'action': 'typing'
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.json().get('ok', False)
        except:
            return False

    def handle_message(self, user_id: int, chat_id: int, text: str, update: dict[str, Any]) -> None:
        """
        Handle incoming Telegram message.
        
        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            text: Message text
            update: Full Telegram update object
        """
        text = text.strip()

        # Handle commands
        if text.startswith('/'):
            self.handle_command(user_id, chat_id, text)
        else:
            # Handle regular text (context-aware)
            self.handle_text(user_id, chat_id, text)

    def handle_command(self, user_id: int, chat_id: int, command: str) -> None:
        """Handle Telegram commands."""
        command = command.lower().split()[0]  # Get first word

        if command == '/start':
            self.send_welcome(chat_id)

        elif command == '/help':
            self.send_help(chat_id)

        # Agri commands
        elif command in ['/register', '/farmer']:
            from aos.adapters.telegram_state import TelegramStateManager
            state_manager = TelegramStateManager()
            state_manager.set_state(chat_id, "register_name", {})
            self.send_message(chat_id, "🌾 <b>Farmer Registration</b>\n\nWhat's your name?")

        elif command == '/harvest':
            self.send_harvest_menu(chat_id)

        # Transport commands
        elif command == '/routes':
            self.send_routes_list(chat_id)

        elif command == '/book':
            self.send_booking_menu(chat_id)

        else:
            self.send_message(chat_id, f"❓ Unknown command: {command}\n\nUse /help to see available commands")

    def handle_text(self, user_id: int, chat_id: int, text: str) -> None:
        """Handle regular text messages (context-aware)."""
        # Get current state
        from aos.adapters.telegram_state import TelegramStateManager
        state_manager = TelegramStateManager()
        user_state = state_manager.get_state(chat_id)

        if not user_state:
            # No active conversation
            self.send_message(chat_id, f"You said: {text}\n\nUse /help to see available commands")
            return

        state = user_state.get("state")
        data = user_state.get("data", {})

        # Handle farmer registration flow
        if state == "register_name":
            data["name"] = text
            state_manager.set_state(chat_id, "register_phone", data)
            self.send_message(chat_id, "Great! What's your phone number?")

        elif state == "register_phone":
            data["phone"] = text
            state_manager.set_state(chat_id, "register_village", data)
            self.send_message(chat_id, "Which village are you from?")

        elif state == "register_village":
            data["village"] = text
            state_manager.set_state(chat_id, "register_roles", data)

            # Show role selection keyboard
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "🌾 Farmer", "callback_data": "role_farmer"},
                        {"text": "🚌 Driver", "callback_data": "role_driver"}
                    ],
                    [
                        {"text": "👤 Passenger", "callback_data": "role_passenger"},
                        {"text": "🛒 Buyer", "callback_data": "role_buyer"}
                    ],
                    [
                        {"text": "✅ Done", "callback_data": "role_done"}
                    ]
                ]
            }

            self.send_message(chat_id,
                "<b>Select your roles</b>\n\n"
                "You can select multiple roles.\n"
                "Click ✅ Done when finished.",
                reply_markup=keyboard
            )

        # Handle harvest quantity input
        elif state == "harvest_quantity":
            try:
                quantity = float(text)
                crop = data.get("crop", "Unknown")

                if self.agri_module:
                    # TODO: Call agri_module.record_harvest(farmer_id, crop, quantity)
                    harvest_id = f"HV-{chat_id}-{int(datetime.now().timestamp())}"
                    self.send_message(chat_id,
                        f"✅ <b>Harvest recorded!</b>\n\n"
                        f"Harvest ID: {harvest_id}\n"
                        f"Crop: {crop}\n"
                        f"Quantity: {quantity} bags\n\n"
                        f"Use /harvest to record another"
                    )
                else:
                    self.send_message(chat_id, f"✅ Recorded: {quantity} bags of {crop}")

                state_manager.clear_state(chat_id)
            except ValueError:
                self.send_message(chat_id, "❌ Please enter a valid number")

        # Handle booking passenger count
        elif state == "booking_passengers":
            try:
                passengers = int(text)
                route = data.get("route", "Unknown")

                if self.transport_module:
                    # TODO: Call transport_module.create_booking(route_id, passengers)
                    booking_id = f"BK-{chat_id}-{int(datetime.now().timestamp())}"
                    self.send_message(chat_id,
                        f"✅ <b>Booking confirmed!</b>\n\n"
                        f"Booking ID: {booking_id}\n"
                        f"Route: {route}\n"
                        f"Passengers: {passengers}\n\n"
                        f"Use /book to make another booking"
                    )
                else:
                    self.send_message(chat_id, f"✅ Booked: {passengers} passengers on {route}")

                state_manager.clear_state(chat_id)
            except ValueError:
                self.send_message(chat_id, "❌ Please enter a valid number")

        else:
            self.send_message(chat_id, "Use /help to see available commands")

    def send_welcome(self, chat_id: int) -> None:
        """Send welcome message."""
        message = """
🌍 <b>Welcome to Africa Offline OS (A-OS)!</b>

A-OS helps farmers and drivers manage their work offline.

<b>🌾 For Farmers:</b>
/register - Register as a farmer
/harvest - Record your harvest
/status - Check your status

<b>🚌 For Transport:</b>
/routes - View available routes
/book - Book a seat
/status - Check your bookings

<b>ℹ️ Help:</b>
/help - Show this message

<i>A-OS works offline and syncs when connected!</i>
"""
        self.send_message(chat_id, message.strip())

    def send_help(self, chat_id: int) -> None:
        """Send help message."""
        self.send_welcome(chat_id)

    def send_harvest_menu(self, chat_id: int) -> None:
        """Send harvest recording menu with inline keyboard."""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🌽 Maize", "callback_data": "harvest_maize"},
                    {"text": "🫘 Beans", "callback_data": "harvest_beans"}
                ],
                [
                    {"text": "☕ Coffee", "callback_data": "harvest_coffee"},
                    {"text": "🌾 Sorghum", "callback_data": "harvest_sorghum"}
                ]
            ]
        }

        message = "📦 <b>Record Harvest</b>\n\nSelect your crop type:"
        self.send_message(chat_id, message, reply_markup=keyboard)

    def send_routes_list(self, chat_id: int) -> None:
        """Send list of available routes."""
        # TODO: Get real routes from TransportModule
        message = """
🚌 <b>Available Routes</b>

1. Nairobi → Nakuru (KES 500)
2. Nairobi → Kisumu (KES 800)
3. Nakuru → Eldoret (KES 400)

Use /book to reserve a seat
"""
        self.send_message(chat_id, message.strip())

    def send_booking_menu(self, chat_id: int) -> None:
        """Send booking menu with inline keyboard."""
        keyboard = {
            "inline_keyboard": [
                [{"text": "Nairobi → Nakuru", "callback_data": "book_route_1"}],
                [{"text": "Nairobi → Kisumu", "callback_data": "book_route_2"}],
                [{"text": "Nakuru → Eldoret", "callback_data": "book_route_3"}]
            ]
        }

        message = "🚌 <b>Book a Seat</b>\n\nSelect your route:"
        self.send_message(chat_id, message, reply_markup=keyboard)

    def handle_callback(self, user_id: int, chat_id: int, callback_data: str) -> None:
        """Handle inline keyboard button clicks."""
        logger.info(f"Callback from {user_id}: {callback_data}")


        from aos.adapters.telegram_state import TelegramStateManager
        from aos.core.users import UniversalUserService
        state_manager = TelegramStateManager()
        user_service = UniversalUserService()

        # Handle role selection during registration
        if callback_data.startswith('role_'):
            user_state = state_manager.get_state(chat_id)
            if user_state and user_state.get("state") == "register_roles":
                data = user_state.get("data", {})

                if callback_data == "role_done":
                    # Complete registration
                    roles = data.get("roles", [])
                    if not roles:
                        self.send_message(chat_id, "❌ Please select at least one role")
                        return

                    user = user_service.register_user(
                        chat_id=chat_id,
                        phone=data["phone"],
                        name=data["name"],
                        village=data.get("village"),
                        roles=roles
                    )

                    if user:
                        role_names = {
                            "farmer": "🌾 Farmer",
                            "driver": "🚌 Driver",
                            "passenger": "👤 Passenger",
                            "buyer": "🛒 Buyer"
                        }
                        roles_text = ", ".join([role_names.get(r, r) for r in roles])

                        self.send_message(chat_id,
                            f"✅ <b>Registration Complete!</b>\n\n"
                            f"Name: {user['name']}\n"
                            f"Phone: {user['phone']}\n"
                            f"Village: {user['village']}\n"
                            f"Roles: {roles_text}\n\n"
                            f"<b>Available Commands:</b>\n"
                            f"{'/harvest - Record harvest' if 'farmer' in roles else ''}\n"
                            f"{'/routes - View routes' if 'driver' in roles or 'passenger' in roles else ''}\n"
                            f"{'/book - Book transport' if 'passenger' in roles else ''}\n"
                            f"/profile - View/edit your profile"
                        )
                        state_manager.clear_state(chat_id)
                    else:
                        self.send_message(chat_id, "❌ Registration failed. Phone number may already be registered.")
                        state_manager.clear_state(chat_id)
                else:
                    # Toggle role
                    role = callback_data.replace('role_', '')
                    roles = data.get("roles", [])

                    if role in roles:
                        roles.remove(role)
                    else:
                        roles.append(role)

                    data["roles"] = roles
                    state_manager.set_state(chat_id, "register_roles", data)

                    # Update message with selected roles
                    role_names = {
                        "farmer": "🌾 Farmer",
                        "driver": "🚌 Driver",
                        "passenger": "👤 Passenger",
                        "buyer": "🛒 Buyer"
                    }
                    selected = [role_names.get(r, r) for r in roles]
                    selected_text = ", ".join(selected) if selected else "None"

                    self.send_message(chat_id,
                        f"<b>Selected roles:</b> {selected_text}\n\n"
                        f"Click more roles or ✅ Done to finish"
                    )
                return

        # Handle harvest callbacks
        if callback_data.startswith('harvest_'):
            crop = callback_data.replace('harvest_', '').capitalize()
            state_manager.set_state(chat_id, "harvest_quantity", {"crop": crop})
            self.send_message(chat_id, f"✅ Selected: {crop}\n\nHow many bags?")

        # Handle booking callbacks
        elif callback_data.startswith('book_route_'):
            route_id = callback_data.replace('book_route_', '')
            route_names = {
                "1": "Nairobi → Nakuru",
                "2": "Nairobi → Kisumu",
                "3": "Nakuru → Eldoret"
            }
            route_name = route_names.get(route_id, "Unknown")
            state_manager.set_state(chat_id, "booking_passengers", {"route": route_name, "route_id": route_id})
            self.send_message(chat_id, f"✅ Route: {route_name}\n\nHow many passengers?")
