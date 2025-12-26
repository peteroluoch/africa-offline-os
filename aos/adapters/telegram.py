"""
Telegram Bot Adapter for A-OS
Handles Telegram bot interactions with domain-aware routing.
"""
from __future__ import annotations

import logging
import os
import requests
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from aos.adapters.domain_router import DomainRouter

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule

logger = logging.getLogger(__name__)

class TelegramAdapter:
    """
    Telegram Bot Adapter for A-OS.
    Features a DomainRouter for scalable, context-aware command handling.
    """

    def __init__(
        self,
        event_bus: EventDispatcher,
        agri_module: Optional[AgriModule] = None,
        transport_module: Optional[TransportModule] = None
    ):
        self.event_bus = event_bus
        self.agri_module = agri_module
        self.transport_module = transport_module
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - Telegram bot disabled")
        
        # Initialize Domain Router
        self.router = DomainRouter(self)
        
        # Set persistent bot commands in the Telegram UI
        self._set_bot_commands()

    def _set_bot_commands(self):
        """Register primary commands with the Telegram API for the 'Menu' button."""
        commands = [
            {"command": "start", "description": "Welcome & Quick Start"},
            {"command": "register", "description": "Create Your Profile"},
            {"command": "domain", "description": "Switch Service Domain"},
            {"command": "profile", "description": "View Your Profile"},
            {"command": "help", "description": "Get Help"}
        ]
        try:
            requests.post(f"{self.api_url}/setMyCommands", json={"commands": commands})
        except Exception as e:
            logger.error(f"Error setting bot commands: {e}")

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram chat."""
        if not self.bot_token:
            return False
            
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json().get('ok', False)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def send_chat_action(self, chat_id: int, action: str = "typing") -> bool:
        """Send a chat action indicator (e.g., typing)."""
        if not self.bot_token:
            return False
        url = f"{self.api_url}/sendChatAction"
        try:
            requests.post(url, json={'chat_id': chat_id, 'action': action}, timeout=5)
            return True
        except:
            return False

    def handle_message(self, message: Dict[str, Any]) -> None:
        """Entry point for incoming messages."""
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        text = message.get('text', '').strip()
        
        if not chat_id or not text:
            return
            
        self.send_chat_action(chat_id)
        
        if text.startswith('/'):
            # It's a command
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:]
            
            # 1. Handle Global Core Commands
            if command == '/start':
                self.send_welcome(chat_id)
            elif command == '/register':
                self._start_registration(chat_id)
            elif command == '/profile':
                self._show_profile(chat_id)
            elif command == '/help':
                self.send_help(chat_id)
            elif command == '/domain':
                self.router.show_domain_selector(chat_id)
            else:
                # 2. Route to Active Domain
                handled = self.router.route_command(chat_id, command, args)
                if not handled:
                    self.send_message(chat_id, f"❓ Unknown command: {command}\n\nUse /domain to select a service or /help for info.")
        else:
            # It's regular text (likely part of a registration or domain-specific prompt)
            self._handle_conversational_text(user_id, chat_id, text)

    def _handle_conversational_text(self, user_id: int, chat_id: int, text: str):
        """Handle context-aware text inputs."""
        from aos.adapters.telegram_state import TelegramStateManager
        state_manager = TelegramStateManager()
        user_state = state_manager.get_state(chat_id)
        
        if not user_state:
            # Fallback - echo or suggest commands
            self.send_message(chat_id, "Use /domain to start a service or /help for a list of commands.")
            return
            
        state = user_state.get("state")
        data = user_state.get("data", {})
        
        # Registration Flow (Enterprise Grade - Multi-step state machine)
        if state == "register_name":
            data["name"] = text
            state_manager.set_state(chat_id, "register_phone", data)
            self.send_message(chat_id, "📱 Great! What is your <b>phone number</b>?")
        
        elif state == "register_phone":
            data["phone"] = text
            state_manager.set_state(chat_id, "register_town", data)
            self.send_message(chat_id, "🏙️ Which <b>Town or City</b> are you nearest to?")
        
        elif state == "register_town":
            data["town"] = text
            state_manager.set_state(chat_id, "register_roles", data)
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🌾 Farmer", "callback_data": "role_farmer"}, {"text": "🚌 Driver", "callback_data": "role_driver"}],
                    [{"text": "👤 Passenger", "callback_data": "role_passenger"}, {"text": "🛒 Buyer", "callback_data": "role_buyer"}],
                    [{"text": "✅ Done", "callback_data": "role_done"}]
                ]
            }
            self.send_message(chat_id, "🎗️ <b>One last step!</b>\n\nSelect your roles (you can pick multiple):", reply_markup=keyboard)
            
        else:
            # If not in a core registration state, it might be a domain-specific conversational state
            # Here we could delegate to the router, but for now we'll keep it simple
            # As modules grow, we can add a router.handle_text method.
            pass

    def handle_callback(self, user_id: int, chat_id: int, callback_data: str) -> None:
        """Entry point for inline button clicks."""
        # 1. Routing to DomainRouter first
        if self.router.route_callback(chat_id, callback_data):
            return

        # 2. Registration roles
        if callback_data.startswith('role_'):
             self._handle_role_callback(chat_id, callback_data)

    def _handle_role_callback(self, chat_id: int, callback_data: str):
        from aos.adapters.telegram_state import TelegramStateManager
        from aos.core.users import UniversalUserService
        state_manager = TelegramStateManager()
        user_service = UniversalUserService()
        
        user_state = state_manager.get_state(chat_id)
        if not user_state or user_state.get("state") != "register_roles":
            return
            
        data = user_state.get("data", {})
        if callback_data == "role_done":
            roles = data.get("roles", [])
            if not roles:
                self.send_message(chat_id, "❌ Please select at least one role before finishing.")
                return
            
            user = user_service.register_user(
                chat_id=chat_id,
                phone=data["phone"],
                name=data["name"],
                town=data.get("town"),
                roles=roles
            )
            
            if user:
                self.send_message(chat_id, f"✅ <b>Welcome to A-OS, {user['name']}!</b>\n\nYour profile is ready. Use /domain to start.")
                state_manager.clear_state(chat_id)
                self.router.show_domain_selector(chat_id)
            else:
                self.send_message(chat_id, "❌ Registration failed. Perhaps your phone number is already in use?")
        else:
            role = callback_data.replace('role_', '')
            roles = data.get("roles", [])
            if role in roles:
                roles.remove(role)
            else:
                roles.append(role)
            data["roles"] = roles
            state_manager.set_state(chat_id, "register_roles", data)
            
            roles_text = ", ".join(roles) if roles else "None"
            self.send_message(chat_id, f"Selected: {roles_text}\n\nSelect more or click ✅ Done.")

    def _start_registration(self, chat_id: int):
        from aos.adapters.telegram_state import TelegramStateManager
        state_manager = TelegramStateManager()
        state_manager.set_state(chat_id, "register_name", {})
        self.send_message(chat_id, "🏁 <b>Registration Started</b>\n\nWhat is your <b>full name</b>?")

    def send_welcome(self, chat_id: int):
        welcome_text = (
            "🌍 <b>Welcome to Africa Offline OS (A-OS)</b>\n\n"
            "One platform for farming, transport, health, and community services. "
            "Works offline and syncs when connected!\n\n"
            "🚀 <b>Quick Start:</b>\n"
            "👋 New here? Use /register to join.\n"
            "📂 Already member? Use /domain to select a service.\n"
            "👤 Use /profile to see your settings."
        )
        self.send_message(chat_id, welcome_text)

    def send_help(self, chat_id: int):
        from aos.core.users import UniversalUserService
        user_service = UniversalUserService()
        active_domain = user_service.get_active_domain(chat_id)
        
        if active_domain:
            self.router.show_domain_help(chat_id, active_domain)
        else:
            help_text = (
                "❓ <b>Core Commands:</b>\n\n"
                "/start - Welcome screen\n"
                "/register - Account registration\n"
                "/domain - Select active service\n"
                "/profile - View your account info\n\n"
                "<i>Select a domain to see specific service commands!</i>"
            )
            self.send_message(chat_id, help_text)

    def _show_profile(self, chat_id: int):
        from aos.core.users import UniversalUserService
        user_service = UniversalUserService()
        user = user_service.get_user_by_chat_id(chat_id)
        
        if not user:
            self.send_message(chat_id, "Account not found. Use /register to create one.")
            return
            
        profile_text = (
            "👤 <b>A-OS Profile</b>\n\n"
            f"<b>Name:</b> {user['name']}\n"
            f"<b>Phone:</b> {user['phone']}\n"
            f"<b>Town:</b> {user['town']}\n"
            f"<b>Roles:</b> {', '.join(user['roles'])}\n"
            f"<b>Active Domain:</b> {user.get('active_domain', 'None')}\n\n"
            "Switch services using /domain."
        )
        self.send_message(chat_id, profile_text)
