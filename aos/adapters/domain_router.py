"""
Domain Router
Handles dispatching commands to the appropriate domain module.
"""
import logging
from typing import Dict, Optional, List
from aos.adapters.domains.base import BaseDomain
from aos.adapters.domains.agri_domain import AgriDomain
from aos.adapters.domains.transport_domain import TransportDomain
from aos.adapters.domains.community_domain import CommunityDomain
from aos.core.users import UniversalUserService

logger = logging.getLogger(__name__)

class DomainRouter:
    """Routes commands based on user's active domain."""
    
    def __init__(self, adapter):
        self.adapter = adapter
        self.user_service = UniversalUserService()
        
        # Register domains
        self.domains: Dict[str, BaseDomain] = {
            "agriculture": AgriDomain(adapter),
            "transport": TransportDomain(adapter),
            "community": CommunityDomain(adapter)
        }
    
    def route_command(self, chat_id: int, command: str, args: List[str]) -> bool:
        """Find the active domain and route the command."""
        active_domain_name = self.user_service.get_active_domain(chat_id)
        
        if not active_domain_name:
            # User has no active domain, show domain selector
            self.show_domain_selector(chat_id)
            return True
        
        domain = self.domains.get(active_domain_name)
        if domain:
            # First check if it's the domain switch command
            if command == "/domain":
                self.show_domain_selector(chat_id)
                return True
                
            # Try to handle in active domain
            handled = domain.handle_command(chat_id, command, args)
            if not handled:
                # Command not recognized in domain, check if it's a global command
                return False
            return True
        
        return False
    
    def route_callback(self, chat_id: int, callback_data: str) -> bool:
        """Route callback data to the appropriate domain."""
        # Check for domain switch callbacks first
        if callback_data.startswith('switch_domain_'):
            domain_name = callback_data.replace('switch_domain_', '')
            self.user_service.set_active_domain(chat_id, domain_name)
            domain = self.domains.get(domain_name)
            display_name = domain.display_name if domain else domain_name
            self.adapter.send_message(chat_id, f"✅ Switched to <b>{display_name}</b> domain.")
            # Show domain-specific help
            self.show_domain_help(chat_id, domain_name)
            return True
            
        # Route to active domain
        active_domain_name = self.user_service.get_active_domain(chat_id)
        domain = self.domains.get(active_domain_name)
        if domain:
            return domain.handle_callback(chat_id, callback_data)
            
        return False

    def show_domain_selector(self, chat_id: int):
        """Show domain selection keyboard."""
        user = self.user_service.get_user_by_chat_id(chat_id)
        if not user:
            # If user not registered, they should register first
            self.adapter.send_message(chat_id, "Welcome! Please use /register to create your profile first.")
            return

        user_roles = user.get('roles', [])
        
        # Build options based on registered roles OR show all if you want to be generic
        keyboard_buttons = []
        for name, domain in self.domains.items():
            keyboard_buttons.append([{"text": domain.display_name, "callback_data": f"switch_domain_{name}"}])
        
        keyboard = {"inline_keyboard": keyboard_buttons}
        self.adapter.send_message(chat_id, "📂 <b>Select Active Domain</b>\n\nChoose the service you want to use right now:", reply_markup=keyboard)

    def show_domain_help(self, chat_id: int, domain_name: str):
        """Show help for a specific domain."""
        domain = self.domains.get(domain_name)
        if not domain:
            return
            
        commands = domain.get_commands()
        help_text = f"<b>{domain.display_name} Commands:</b>\n\n"
        for cmd in commands:
            help_text += f"/{cmd['command']} - {cmd['description']}\n"
        
        help_text += "\n/domain - Switch to another domain\n"
        help_text += "/profile - View your profile"
        
        self.adapter.send_message(chat_id, help_text)
