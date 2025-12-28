"""
Transport Domain
Handles all mobility and logistics related commands.
"""
from typing import List, Dict
import logging
from aos.adapters.domains.base import BaseDomain

logger = logging.getLogger(__name__)

class TransportDomain(BaseDomain):
    """Transport domain logic v2 (Mobility Intelligence)."""
    
    @property
    def name(self) -> str:
        return "transport"
    
    @property
    def display_name(self) -> str:
        return "🚌 Transport-Pulse"
    
    def get_commands(self) -> List[Dict[str, str]]:
        return [
            {"command": "zones", "description": "View mobility zones"},
            {"command": "avoid", "description": "Roads to avoid (Signals)"},
            {"command": "state", "description": "Check road/zone intelligence"},
            {"command": "report", "description": "Report traffic or availability"}
        ]
    
    async def handle_command(self, chat_id: int, command: str, args: List[str]) -> bool:
        if not getattr(self.adapter, "transport_module", None):
            await self.adapter.send_message(str(chat_id), "⚠️ Transport module not initialized")
            return True

        if command == "/zones":
            return await self._handle_zones(chat_id)
        elif command == "/avoid":
            return await self._handle_avoid(chat_id)
        elif command == "/state":
            return await self._handle_state(chat_id, args)
        elif command == "/report":
            return await self._handle_report_prompt(chat_id)
        elif command == "/routes": # Shim
            return await self._handle_zones(chat_id)
        elif command == "/traffic":
            return await self._handle_traffic_report(chat_id, args)
        elif command == "/avl":
            return await self._handle_availability_report(chat_id, args)
            
        return False
    
    async def handle_callback(self, chat_id: int, callback_data: str) -> bool:
        if callback_data.startswith('view_zone_'):
            zone_id = callback_data.replace('view_zone_', '')
            return await self._show_zone_state(chat_id, zone_id)
        return False

    async def _handle_zones(self, chat_id: int) -> bool:
        """List transport zones."""
        zones = self.adapter.transport_module.discover_zones()
        if not zones:
            await self.adapter.send_message(str(chat_id), "📭 No transport zones registered.")
            return True

        message = "🚌 <b>Transport Zones</b>\n\n"
        keyboard_buttons = []
        for zone in zones[:8]:
            message += f"• {zone.name} ({zone.type})\n"
            keyboard_buttons.append([{"text": f"🔍 {zone.name}", "callback_data": f"view_zone_{zone.id}"}])

        keyboard = {"inline_keyboard": keyboard_buttons}
        await self.adapter.send_message(str(chat_id), message, metadata={"reply_markup": keyboard})
        return True

    async def _handle_avoid(self, chat_id: int) -> bool:
        """Show blocked or slow zones."""
        zones = self.adapter.transport_module.discover_zones()
        blocked_zones = []
        
        for zone in zones:
            intel = self.adapter.transport_module.get_zone_intelligence(zone.id)
            if intel.get("current_state") in ["blocked", "slow"]:
                blocked_zones.append(intel)

        if not blocked_zones:
            await self.adapter.send_message(str(chat_id), "✅ <b>All systems flowing!</b>\nNo blocked or slow roads reported.")
            return True

        message = "🚨 <b>Roads to Avoid</b>\n\n"
        for item in blocked_zones:
            icon = "🛑" if item["current_state"] == "blocked" else "⚠️"
            message += f"{icon} <b>{item['zone_name']}</b>: {item['current_state'].upper()}\n"
            
        await self.adapter.send_message(str(chat_id), message)
        return True

    async def _handle_state(self, chat_id: int, args: List[str]) -> bool:
        """Check specific zone intelligence."""
        if not args:
            await self.adapter.send_message(str(chat_id), "🔍 Usage: /state [zone_name]")
            return True
            
        search = " ".join(args)
        zones = self.adapter.transport_module.discover_zones(location_scope=search)
        if not zones:
            # Try name match
            all_zones = self.adapter.transport_module.discover_zones()
            zones = [z for z in all_zones if search.lower() in z.name.lower()]

        if not zones:
            await self.adapter.send_message(str(chat_id), f"📭 Zone '{search}' not found.")
            return True

        return await self._show_zone_state(chat_id, zones[0].id)

    async def _show_zone_state(self, chat_id: int, zone_id: str) -> bool:
        """Show detailed intelligence for a zone."""
        intel = self.adapter.transport_module.get_zone_intelligence(zone_id)
        if not intel:
            return False

        states = {"flowing": "🟢", "slow": "🟡", "blocked": "🔴", "unknown": "⚪"}
        state_icon = states.get(intel.get("current_state", "unknown"), "⚪")
        
        message = f"🚌 <b>{intel['zone_name']}</b>\n"
        message += f"State: {state_icon} {intel['current_state'].upper()}\n"
        message += f"Confidence: {intel['confidence']:.1f}\n\n"
        
        if intel.get("availability"):
            message += "<b>Vehicle Availability:</b>\n"
            for avail in intel["availability"]:
                message += f"• To {avail['destination']}: {avail['availability_state'].upper()}\n"
        else:
            message += "<i>No vehicles reported recently.</i>"

        await self.adapter.send_message(str(chat_id), message)
        return True

    async def _handle_report_prompt(self, chat_id: int) -> bool:
        """Prompt to report traffic/availability."""
        await self.adapter.send_message(
            str(chat_id), 
            "📢 <b>Mobility Report</b>\n\n"
            "Reports are verified by the community.\n\n"
            "To report traffic:\n<code>/traffic [zone] [flowing|slow|blocked]</code>\n\n"
            "To report vehicles:\n<code>/avl [zone] [destination] [available|limited|none]</code>"
        )
        return True

    async def _handle_traffic_report(self, chat_id: int, args: List[str]) -> bool:
        """Handle traffic report command."""
        if len(args) < 2:
            await self.adapter.send_message(str(chat_id), "❌ Usage: /traffic [zone_name] [flowing|slow|blocked]")
            return True
            
        state = args[-1].lower()
        zone_search = " ".join(args[:-1])
        
        if state not in ["flowing", "slow", "blocked"]:
            await self.adapter.send_message(str(chat_id), "❌ Invalid state. Use: flowing, slow, or blocked.")
            return True

        all_zones = self.adapter.transport_module.discover_zones()
        target_zone = next((z for z in all_zones if zone_search.lower() in z.name.lower()), None)
        
        if not target_zone:
            await self.adapter.send_message(str(chat_id), f"📭 Zone '{zone_search}' not found.")
            return True

        success = self.adapter.transport_module.report_traffic_signal(
            zone_id=target_zone.id,
            state=state,
            source=f"tg_{chat_id}"
        )
        
        if success:
            await self.adapter.send_message(str(chat_id), f"✅ Traffic report for <b>{target_zone.name}</b> recorded.")
        else:
            await self.adapter.send_message(str(chat_id), "❌ Failed to record report.")
        return True

    async def _handle_availability_report(self, chat_id: int, args: List[str]) -> bool:
        """Handle availability report command."""
        if len(args) < 3:
            await self.adapter.send_message(str(chat_id), "❌ Usage: /avl [zone_name] [destination] [available|limited|none]")
            return True
            
        state = args[-1].lower()
        destination = args[-2]
        zone_search = " ".join(args[:-2])
        
        if state not in ["available", "limited", "none"]:
            await self.adapter.send_message(str(chat_id), "❌ Invalid state. Use: available, limited, or none.")
            return True

        all_zones = self.adapter.transport_module.discover_zones()
        target_zone = next((z for z in all_zones if zone_search.lower() in z.name.lower()), None)
        
        if not target_zone:
            await self.adapter.send_message(str(chat_id), f"📭 Zone '{zone_search}' not found.")
            return True

        success = self.adapter.transport_module.report_availability(
            zone_id=target_zone.id,
            destination=destination,
            state=state,
            source=f"tg_{chat_id}"
        )
        
        if success:
            await self.adapter.send_message(str(chat_id), f"✅ Availability to <b>{destination}</b> from <b>{target_zone.name}</b> recorded.")
        else:
            await self.adapter.send_message(str(chat_id), "❌ Failed to record report.")
        return True
