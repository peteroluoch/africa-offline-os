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
from aos.adapters.telegram_gateway import TelegramGateway
from aos.core.channels.base import ChannelAdapter, ChannelRequest, ChannelResponse, ChannelType
from aos.core.utils.phone import normalize_phone

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule
    from aos.modules.community import CommunityModule

logger = logging.getLogger(__name__)

class TelegramAdapter(ChannelAdapter):
    """
    Telegram Bot Adapter for A-OS.
    Features a DomainRouter for scalable, context-aware command handling.
    """

    def __init__(
        self,
        event_bus: EventDispatcher,
        agri_module: Optional[AgriModule] = None,
        transport_module: Optional[TransportModule] = None,
        community_module: Optional[CommunityModule] = None,
        gateway: Optional[TelegramGateway] = None
    ):
        self.event_bus = event_bus
        self.agri_module = agri_module
        self.transport_module = transport_module
        self.community_module = community_module
        
        # Inject or create gateway for API interactions
        self.gateway = gateway or TelegramGateway()
        
        if not self.gateway.bot_token:
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
            # Note: We still use requests here briefly for setup, or we could move this to the gateway
            # For strict compliance, moving setup to gateway might be better, but gateway usually handles 'messages'.
            # Let's use the gateway's token/url.
            url = f"{self.gateway.base_url}/setMyCommands"
            requests.post(url, json={"commands": commands})
        except Exception as e:
            logger.error(f"Error setting bot commands: {e}")

    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        """Standardized outbound message send using the gateway."""
        # Normalize to string if it somehow isn't
        chat_id = str(to)
        
        # Send via gateway
        response = await self.gateway.send(chat_id, message, metadata=metadata)
        return response.get("ok", False)

    def parse_request(self, payload: dict[str, Any]) -> ChannelRequest:
        """Standardized request parsing."""
        message = payload.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        sender = str(message.get("from", {}).get("id", ""))
        text = message.get("text", "")

        return ChannelRequest(
            session_id=chat_id,
            sender=sender,
            content=text,
            channel_type="telegram",
            raw_payload=payload
        )

    def format_response(self, response: ChannelResponse) -> dict[str, Any]:
        """Standardized response formatting."""
        return {
            "text": response.content,
            "parse_mode": "HTML"
        }

    def get_channel_type(self) -> str:
        return "telegram"

    def send_chat_action(self, chat_id: int, action: str = "typing") -> bool:
        """Send a chat action indicator indicator via gateway."""
        return self.gateway.send_chat_action(str(chat_id), action)

    async def handle_message(self, message: Dict[str, Any]) -> None:
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
                if args:
                    # Deep link join: /start <slug>
                    # Auditor Alignment: Support human-readable slugs
                    slug = args[0]
                    # Strip 'join_' prefix if present (backwards compatibility)
                    if slug.startswith('join_'):
                        slug = slug.replace('join_', '')
                    await self._handle_community_join_request(chat_id, slug)
                else:
                    await self.send_welcome(chat_id)
            elif command == '/myid':
                # Surgical Phase 1: Only echo ID, no storage or registration
                chat_type = message.get('chat', {}).get('type')
                if chat_type == 'private':
                    await self.send_message(
                        str(chat_id),
                        f"Your Telegram ID is: <code>{chat_id}</code>\n\n"
                        "Share this ID with your community admin if they need to add you manually."
                    )
                else:
                    await self.send_message(
                        str(chat_id),
                        "Please send /myid in a private chat with the bot."
                    )
            elif command == '/register':
                await self._start_registration(chat_id)
            elif command == '/profile':
                await self._show_profile(chat_id)
            elif command == '/help':
                await self.send_help(chat_id)
            elif command == '/domain':
                await self.router.show_domain_selector(chat_id)
            else:
                # 2. Route to Active Domain
                handled = await self.router.route_command(chat_id, command, args)
                if not handled:
                    await self.send_message(str(chat_id), f"❓ Unknown command: {command}\n\nUse /domain to select a service or /help for info.")
        else:
            # It's regular text (likely part of a registration or domain-specific prompt)
            await self._handle_conversational_text(user_id, chat_id, text)

    async def _handle_conversational_text(self, user_id: int, chat_id: int, text: str):
        """Handle context-aware text inputs."""
        from aos.adapters.telegram_state import TelegramStateManager
        state_manager = TelegramStateManager()
        user_state = state_manager.get_state(chat_id)
        
        # Phase 3: Check if text matches a community code FIRST
        # This must happen before state checks so it works for all users
        potential_code = text.strip().upper()
        group = self.community_module.get_group_by_code(potential_code)
        
        if group:
            # Valid community code detected
            await self._handle_community_join_request_by_code(chat_id, group)
            return
        
        if not user_state:
            # Fallback - echo or suggest commands
            await self.send_message(str(chat_id), "Use /domain to start a service or /help for a list of commands.")
            return
            
        state = user_state.get("state")
        data = user_state.get("data", {})
        
        # Registration Flow (Enterprise Grade - Multi-step state machine)
        if state == "register_name":
            data["name"] = text
            state_manager.set_state(chat_id, "register_phone", data)
            await self.send_message(str(chat_id), "📱 Great! What is your <b>phone number</b>?")
        
        elif state == "register_phone":
            data["phone"] = text
            state_manager.set_state(chat_id, "register_town", data)
            await self.send_message(str(chat_id), "🏙️ Which <b>Town or City</b> are you nearest to?")
        
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
            await self.send_message(str(chat_id), "🎗️ <b>One last step!</b>\n\nSelect your roles (you can pick multiple):", metadata={"reply_markup": keyboard})
            
        else:
            # If not in a core registration state, it might be a domain-specific conversational state
            # Here we could delegate to the router, but for now we'll keep it simple
            # As modules grow, we can add a router.handle_text method.
            pass

    async def handle_callback(self, user_id: int, chat_id: int, callback_data: str) -> None:
        """Entry point for inline button clicks."""
        # 1. Routing to DomainRouter first
        if await self.router.route_callback(chat_id, callback_data):
            return

        # 2. Community Join Confirmation
        if callback_data.startswith('join_'):
            await self._handle_join_callback(chat_id, callback_data)
            return

        # 3. Registration roles
        if callback_data.startswith('role_'):
             await self._handle_role_callback(chat_id, callback_data)

    async def _handle_role_callback(self, chat_id: int, callback_data: str):
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
                await self.send_message(str(chat_id), "❌ Please select at least one role before finishing.")
                return
            
            user = user_service.register_user(
                chat_id=chat_id,
                phone=data["phone"],
                name=data["name"],
                town=data.get("town"),
                roles=roles
            )
            
            if user:
                await self.send_message(str(chat_id), f"✅ <b>Welcome to A-OS, {user['name']}!</b>\n\nYour profile is ready. Use /domain to start.")
                state_manager.clear_state(chat_id)
                await self.router.show_domain_selector(chat_id)
            else:
                await self.send_message(str(chat_id), "❌ Registration failed. Perhaps your phone number is already in use?")
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
            await self.send_message(str(chat_id), f"Selected: {roles_text}\n\nSelect more or click ✅ Done.")

    async def _start_registration(self, chat_id: int):
        from aos.adapters.telegram_state import TelegramStateManager
        state_manager = TelegramStateManager()
        state_manager.set_state(chat_id, "register_name", {})
        await self.send_message(str(chat_id), "🏁 <b>Registration Started</b>\n\nWhat is your <b>full name</b>?")

    async def send_welcome(self, chat_id: int):
        welcome_text = (
            "🌍 <b>Welcome to Africa Offline OS (A-OS)</b>\n\n"
            "If you have a <b>Community Code</b>, type it now to join.\n\n"
            "Or type /help to learn more about our services."
        )
        await self.send_message(str(chat_id), welcome_text)

    async def send_help(self, chat_id: int):
        from aos.core.users import UniversalUserService
        user_service = UniversalUserService()
        active_domain = user_service.get_active_domain(chat_id)
        
        if active_domain:
            await self.router.show_domain_help(chat_id, active_domain)
        else:
            help_text = (
                "❓ <b>Core Commands:</b>\n\n"
                "/start - Welcome screen\n"
                "/register - Account registration\n"
                "/domain - Select active service\n"
                "/profile - View your account info\n\n"
                "<i>Select a domain to see specific service commands!</i>"
            )
            await self.send_message(str(chat_id), help_text)

    async def _show_profile(self, chat_id: int):
        from aos.core.users import UniversalUserService
        user_service = UniversalUserService()
        user = user_service.get_user_by_chat_id(chat_id)
        
        if not user:
            await self.send_message(str(chat_id), "Account not found. Use /register to create one.")
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
        await self.send_message(str(chat_id), profile_text)

    async def _handle_community_join_request(self, chat_id: int, slug: str):
        """Handle deep link request to join a community via slug."""
        # Auditor Alignment: First try by slug, then by ID (for legacy links)
        group = self.community_module.get_group_by_slug(slug)
        if not group:
            group = self.community_module.get_group(slug)
            
        if not group:
            await self.send_message(str(chat_id), "❌ Sorry, this invite link is invalid or expired.")
            return

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Confirm", "callback_data": f"join_confirm_{group.id}"},
                    {"text": "❌ Cancel", "callback_data": "join_cancel"}
                ]
            ]
        }
        
        message = (
            f"🤝 <b>Community Invitation</b>\n\n"
            f"You are about to join <b>{group.name}</b>.\n"
            f"This will allow the community to send you updates.\n\n"
            f"Do you want to continue?"
        )
        await self.send_message(str(chat_id), message, metadata={"reply_markup": keyboard})

    async def _handle_join_callback(self, chat_id: int, callback_data: str):
        """Process community join confirmation buttons."""
        if callback_data == "join_cancel":
            await self.send_message(str(chat_id), "Join cancelled. Use /domain to browse other services.")
            return
            
        if callback_data.startswith("join_confirm_"):
            community_id = callback_data.replace("join_confirm_", "")
            group = self.community_module.get_group(community_id)
            
            if not group:
                await self.send_message(str(chat_id), "❌ Error: Community no longer exists.")
                return

            # Add member to community
            success = self.community_module.add_member_to_community(
                community_id=community_id,
                user_id=str(chat_id),
                channel="telegram"
            )
            
            if success:
                await self.send_message(
                    str(chat_id), 
                    f"🎉 <b>Success!</b>\n\nYou have joined <b>{group.name}</b>. You will now receive all broadcasts here!"
                )
            else:
                await self.send_message(str(chat_id), "❌ Failed to join. You might already be a member.")

    async def _handle_community_join_request_by_code(self, chat_id: int, group: Any):
        """Handle community join via typed code (Phase 3)."""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Confirm", "callback_data": f"join_confirm_{group.id}"},
                    {"text": "❌ Cancel", "callback_data": "join_cancel"}
                ]
            ]
        }
        
        message = (
            f"🤝 <b>Community Invitation</b>\n\n"
            f"You are about to join <b>{group.name}</b>.\n"
            f"This will allow the community to send you updates.\n\n"
            f"Do you want to continue?"
        )
        await self.send_message(str(chat_id), message, metadata={"reply_markup": keyboard})
