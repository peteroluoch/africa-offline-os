"""
Vehicle Router - Multi-layer command handling.
Separates Global, Core, and Module commands.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from aos.core.institution.service import InstitutionService

logger = logging.getLogger("aos.vehicles")

class CommandRouter:
    """
    Routes incoming messages to the correct logic layer.
    
    Layer 1: Global (Platfrom-specific: /start, /help)
    Layer 2: Core (A-OS Core: /join, /myinfo, /stop)
    Layer 3: Module (Institution-specific: /prayer)
    """

    def __init__(self, institution_service: InstitutionService):
        self.service = institution_service
        self._global_handlers: dict[str, Callable] = {}
        self._core_handlers: dict[str, Callable] = {}
        self._module_handlers: dict[str, Callable] = {}

    def register_global(self, command: str, handler: Callable):
        self._global_handlers[f"/{command.lstrip('/')}"] = handler

    def register_core(self, command: str, handler: Callable):
        self._core_handlers[f"/{command.lstrip('/')}"] = handler

    def register_module(self, command: str, handler: Callable):
        self._module_handlers[f"/{command.lstrip('/')}"] = handler

    async def handle_command(
        self, 
        command_text: str, 
        vehicle_type: str, 
        vehicle_identity: str,
        **context
    ) -> str | None:
        """
        Main entry point for command routing.
        """
        parts = command_text.split()
        if not parts:
            return None
        
        raw_cmd = parts[0].lower()
        args = parts[1:]

        # Layer 1: Global
        if raw_cmd in self._global_handlers:
            return await self._global_handlers[raw_cmd](vehicle_identity, *args, **context)

        # Layer 2: Core
        if raw_cmd in self._core_handlers:
            return await self._core_handlers[raw_cmd](vehicle_identity, *args, **context)

        # Layer 3: Module
        if raw_cmd in self._module_handlers:
            return await self._module_handlers[raw_cmd](vehicle_identity, *args, **context)

        # Default: Unknown
        logger.info(f"Unknown command {raw_cmd} from {vehicle_type}:{vehicle_identity}")
        return "Unknown command. Type /help for assistance."

    # --- Standard Handlers (Layer 2 examples) ---

    async def handle_join(self, vehicle_identity: str, code: str, **context) -> str:
        """/join <code>"""
        # 1. Resolve code to community
        community = self.service.communities.get_by_code(code)
        if not community:
            return f"No active community found for code: '{code}'"

        # 2. Check if already a member
        existing = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        if existing:
            return f"You are already a member of {community.name}."

        # 3. Register
        full_name = context.get("user_name", "Unknown Member")
        self.service.register_member(
            community.id, 
            full_name, 
            context.get("vehicle_type", "telegram"), 
            vehicle_identity
        )
        return f"Successfully joined {community.name}! Welcome."

    async def handle_myinfo(self, vehicle_identity: str, **context) -> str:
        """/myinfo"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        if not member:
            return "You are not registered in any community. Use /join <code> to start."
        
        groups = self.service.get_member_groups(member.id)
        group_names = ", ".join([g.name for g in groups]) if groups else "None"
        
        return (
            f"👤 Member ID: {member.id}\n"
            f"Name: {member.full_name}\n"
            f"Role: {member.role_id}\n"
            f"Groups: {group_names}\n"
            f"Joined: {member.joined_at.strftime('%Y-%m-%d')}"
        )

    # --- Group Commands (PROMPT 6) ---

    async def handle_groups(self, vehicle_identity: str, **context) -> str:
        """/groups"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        if not member: return "Register first with /join <code>"
        
        groups = self.service.list_community_groups(member.community_id)
        if not groups: return "No groups available in this community."
        
        msg = "📂 Available Groups:\n"
        for g in groups:
            msg += f"- {g.name}: {g.description or 'No description'}\n"
        msg += "\nUse /join_group <name> to join."
        return msg

    async def handle_join_group(self, vehicle_identity: str, group_name: str, **context) -> str:
        """/join_group <name>"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        groups = self.service.list_community_groups(member.community_id)
        target = next((g for g in groups if g.name.lower() == group_name.lower()), None)
        
        if not target: return f"Group '{group_name}' not found."
        
        self.service.join_group(member.id, target.id)
        return f"✅ Successfully joined the {target.name} group."

    async def handle_leave_group(self, vehicle_identity: str, group_name: str, **context) -> str:
        """/leave_group <name>"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        groups = self.service.get_member_groups(member.id)
        target = next((g for g in groups if g.name.lower() == group_name.lower()), None)
        
        if not target: return f"You are not a member of '{group_name}'."
        
        self.service.leave_group(member.id, target.id)
        return f"👋 Left the {target.name} group."

    # --- Broadcast Command (PROMPT 7) ---

    async def handle_broadcast(self, vehicle_identity: str, *args, **context) -> str:
        """/broadcast <message body>"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        if not self.service.can_broadcast(member.id):
            return "❌ Unauthorized. Only the Administrator (Pastor) can broadcast."
        
        message = " ".join(args)
        if not message: return "Usage: /broadcast <message>"
        
        # In a real integration, the Router would now call the Vehicle Adapter 
        # to send this to all members. For now, we log it.
        track_id = self.service.log_message(
            member.community_id, member.id, "broadcast", "ALL", 
            context.get("vehicle_type", "telegram"), "announcement", message
        )
        
        return f"📢 Broadcast queued. tracking_id: {track_id[:8]}"

    # --- Prayer Commands (PROMPT 8) ---

    async def handle_prayer(self, vehicle_identity: str, *args, **context) -> str:
        """/prayer <request text>"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        text = " ".join(args)
        if not text: return "Usage: /prayer <your request>"
        
        self.service.submit_prayer_request(member.community_id, member.id, text)
        return "🙏 Prayer request submitted. The Pastor will review and share it."

    async def handle_prayer_list(self, vehicle_identity: str, **context) -> str:
        """/prayer_list (Admin Only)"""
        member = self.service.get_member_by_vehicle(context.get("vehicle_type", "telegram"), vehicle_identity)
        if not self.service.can_broadcast(member.id):
            return "❌ Unauthorized."
        
        prayers = self.service.get_pending_prayers(member.community_id, member.id)
        if not prayers: return "No pending prayer requests."
        
        msg = "🙏 Pending Prayer Requests:\n"
        for p in prayers:
            msg += f"- [{p.id[:8]}] {p.request_text}\n"
        return msg
