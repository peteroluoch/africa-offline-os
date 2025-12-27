from __future__ import annotations

from typing import TYPE_CHECKING
from aos.core.channels.base import ChannelResponse
from aos.core.channels.ussd import USSDSession

if TYPE_CHECKING:
    from aos.modules.community import CommunityModule

class CommunityUSSDHandler:
    """Multi-step USSD handler for community interactions."""

    def __init__(self, community_module: CommunityModule | None = None):
        self.community = community_module

    async def process(self, session: USSDSession, user_input: str) -> ChannelResponse:
        state = session.state
        user_input = user_input.strip()

        if state == "START":
            if not user_input:
                return ChannelResponse(
                    "[A-OS Community]\n1. Latest Announcements\n2. Upcoming Events\n3. Find Group\n4. Group Admin", 
                    True
                )
            if user_input == "1":
                return await self._show_announcements(session)
            if user_input == "2":
                return await self._show_events(session)
            if user_input == "3":
                session.update("FIND_GROUP")
                return self._list_groups_menu()
            if user_input == "4":
                session.update("ADMIN_AUTH")
                return ChannelResponse("Enter Admin PIN:", True)
            
            return ChannelResponse("Invalid selection.", False)

        # --- Discovery Flow ---
        if state == "FIND_GROUP":
            groups = self.community.list_groups() if self.community else []
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(groups):
                    group = groups[idx]
                    session.update("GROUP_VIEW", group_id=group.id)
                    return ChannelResponse(
                        f"[{group.name}]\n1. Services/Times\n2. Announcements\n3. Send Message", 
                        True
                    )
            except:
                pass
            return ChannelResponse("Invalid group.", False)

        if state == "GROUP_VIEW":
            group_id = session.data.get("group_id")
            if user_input == "1":
                return await self._show_events(session, group_id)
            if user_input == "2":
                return await self._show_announcements(session, group_id)
            if user_input == "3":
                session.update("SEND_INQUIRY")
                return ChannelResponse("Type your message for the admin:", True)

        if state == "SEND_INQUIRY":
            # In a real system, we'd notify the admin. Here we check cache.
            group_id = session.data.get("group_id")
            answer = await self.community.handle_inquiry(group_id, user_input)
            if answer:
                return ChannelResponse(f"[Auto-Reply]\n{answer}", False)
            return ChannelResponse("Message sent to admin. You will receive an SMS reply.", False)

        # --- Admin Flow ---
        if state == "ADMIN_AUTH":
            if user_input == "1234": # Simplified for demo
                session.update("ADMIN_MENU")
                return ChannelResponse("Admin Menu:\n1. Send Broadcast\n2. Change Schedule", True)
            return ChannelResponse("Access Denied.", False)

        if state == "ADMIN_MENU":
            if user_input == "1":
                session.update("ADMIN_BROADCAST")
                return ChannelResponse("Type broadcast message:", True)
            return ChannelResponse("Coming soon.", False)

        if state == "ADMIN_BROADCAST":
            group_id = session.data.get("group_id", "ST_MARKS_001") # Default for demo
            if self.community:
                await self.community.create_announcement(group_id, user_input)
                return ChannelResponse("Broadcast sent to all members.", False)
            return ChannelResponse("Error: Module offline.", False)

        return ChannelResponse("Session timeout.", False)

    def _list_groups_menu(self) -> ChannelResponse:
        groups = self.community.list_groups() if self.community else []
        if not groups:
            return ChannelResponse("No groups found nearby.", False)
        
        menu = "Select Group:\n"
        for i, g in enumerate(groups[:5], 1):
            menu += f"{i}. {g.name}\n"
        return ChannelResponse(menu, True)

    async def _show_announcements(self, session: USSDSession, group_id: str | None = None) -> ChannelResponse:
        # For demo, list all recent ones if no group_id
        if not self.community: return ChannelResponse("Offline", False)
        anns = self.community._announcements.list_all()
        if group_id:
            anns = [a for a in anns if a.group_id == group_id]
        
        if not anns:
            return ChannelResponse("No recent announcements.", False)
        
        msg = f"[Announcements]\n{anns[0].message}"
        return ChannelResponse(msg, False)

    async def _show_events(self, session: USSDSession, group_id: str | None = None) -> ChannelResponse:
        if not self.community: return ChannelResponse("Offline", False)
        evts = self.community._events.list_all()
        if group_id:
            evts = [e for e in evts if e.group_id == group_id]
        
        if not evts:
            return ChannelResponse("No upcoming events.", False)
        
        msg = f"[Events]\n{evts[0].title}: {evts[0].start_time.strftime('%H:%M')}"
        return ChannelResponse(msg, False)
