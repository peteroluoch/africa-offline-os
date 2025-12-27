"""
Community Domain Handler for Telegram Bot.
Enables group discovery, event viewing, and inquiry submission via Telegram.
"""
import logging
from typing import List
from aos.adapters.domains.base import BaseDomain

logger = logging.getLogger(__name__)

class CommunityDomain(BaseDomain):
    """Handles Community-related commands in Telegram."""
    
    def __init__(self, adapter):
        super().__init__(adapter)
        self._name = "community"
        self._display_name = "🏘️ Community-Pulse"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def display_name(self) -> str:
        return self._display_name
        
    def get_commands(self) -> List[dict]:
        """Return list of supported commands."""
        return [
            {"command": "groups", "description": "View all registered groups"},
            {"command": "discover", "description": "Find groups by location or type"},
            {"command": "events", "description": "View upcoming events"},
            {"command": "announcements", "description": "Latest community announcements"},
            {"command": "inquiry", "description": "Send a question to a group"}
        ]
    
    def handle_callback(self, chat_id: int, callback_data: str) -> bool:
        """Handle callback queries (not implemented yet)."""
        return False
    
    def get_help_text(self) -> str:
        """Return help text for this domain."""
        return """
🏘️ <b>Community-Pulse Commands</b>

/groups - View all registered groups
/discover - Find groups by location or type
/events - View upcoming events
/announcements - Latest community announcements
/inquiry - Send a question to a group

<i>Groups hold accounts. No individual registration needed.</i>
"""
    
    def handle_command(self, chat_id: int, command: str, args: List[str]) -> bool:
        """Handle community-specific commands."""
        if not self.adapter.community_module:
            self.adapter.send_message(chat_id, "⚠️ Community module not initialized")
            return True
        
        if command == "/groups":
            return self._handle_groups(chat_id)
        elif command == "/discover":
            return self._handle_discover(chat_id, args)
        elif command == "/events":
            return self._handle_events(chat_id)
        elif command == "/announcements":
            return self._handle_announcements(chat_id)
        elif command == "/inquiry":
            return self._handle_inquiry_prompt(chat_id)
        
        return False
    
    def _handle_groups(self, chat_id: int) -> bool:
        """List all registered groups."""
        groups = self.adapter.community_module.list_groups()
        
        if not groups:
            self.adapter.send_message(
                chat_id,
                "📭 No community groups registered yet.\n\n"
                "Groups can register via the web dashboard."
            )
            return True
        
        message = "🏘️ <b>Registered Community Groups</b>\n\n"
        for group in groups[:10]:  # Limit to 10
            tags = group.tags if isinstance(group.tags, str) else "[]"
            message += f"• <b>{group.name}</b>\n"
            message += f"  📍 {group.location or 'Unknown'}\n"
            message += f"  🏷️ {tags}\n"
            message += f"  🔒 Trust: {group.trust_level}\n\n"
        
        if len(groups) > 10:
            message += f"<i>...and {len(groups) - 10} more groups</i>"
        
        self.adapter.send_message(chat_id, message)
        return True
    
    def _handle_discover(self, chat_id: int, args: List[str]) -> bool:
        """Discover groups by location or tags."""
        if not args:
            self.adapter.send_message(
                chat_id,
                "🔍 <b>Group Discovery</b>\n\n"
                "Usage: /discover [location or tag]\n\n"
                "Examples:\n"
                "• /discover Kawangware\n"
                "• /discover church\n"
                "• /discover mosque"
            )
            return True
        
        search_term = " ".join(args)
        
        # Try location search first
        groups = self.adapter.community_module.discover_groups(location=search_term)
        
        # If no results, try tag search
        if not groups:
            groups = self.adapter.community_module.discover_groups(tag_filter=[search_term])
        
        if not groups:
            self.adapter.send_message(
                chat_id,
                f"📭 No groups found matching '{search_term}'"
            )
            return True
        
        message = f"🔍 <b>Groups matching '{search_term}'</b>\n\n"
        for group in groups[:5]:
            message += f"• <b>{group.name}</b>\n"
            message += f"  📍 {group.location}\n\n"
        
        self.adapter.send_message(chat_id, message)
        return True
    
    def _handle_events(self, chat_id: int) -> bool:
        """List upcoming events."""
        events = self.adapter.community_module.list_events()
        
        if not events:
            self.adapter.send_message(
                chat_id,
                "📅 No upcoming events scheduled."
            )
            return True
        
        message = "📅 <b>Upcoming Events</b>\n\n"
        for event in events[:5]:
            group = self.adapter.community_module.get_group(event.group_id)
            group_name = group.name if group else "Unknown Group"
            
            message += f"• <b>{event.title}</b>\n"
            message += f"  🏘️ {group_name}\n"
            message += f"  🕒 {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
            message += f"  🏷️ {event.event_type}\n\n"
        
        self.adapter.send_message(chat_id, message)
        return True
    
    def _handle_announcements(self, chat_id: int) -> bool:
        """List recent announcements."""
        announcements = self.adapter.community_module._announcements.list_all()
        
        if not announcements:
            self.adapter.send_message(
                chat_id,
                "📢 No recent announcements."
            )
            return True
        
        message = "📢 <b>Community Announcements</b>\n\n"
        for ann in announcements[:3]:
            group = self.adapter.community_module.get_group(ann.group_id)
            group_name = group.name if group else "Unknown Group"
            
            urgency_icon = "🚨" if ann.urgency == "urgent" else "ℹ️"
            message += f"{urgency_icon} <b>{group_name}</b>\n"
            message += f"{ann.message}\n\n"
        
        self.adapter.send_message(chat_id, message)
        return True
    
    def _handle_inquiry_prompt(self, chat_id: int) -> bool:
        """Prompt user to send an inquiry."""
        self.adapter.send_message(
            chat_id,
            "💬 <b>Send an Inquiry</b>\n\n"
            "Type your question and I'll check if there's a cached answer.\n\n"
            "Example: 'What time is Sunday service?'"
        )
        # In a real implementation, we'd set a state to capture the next message
        return True
