"""
Sports Communities Plugin

Implements sports-specific features for athletic clubs and teams.
Includes training attendance, match scheduling, and membership dues management.
"""
from __future__ import annotations

from typing import List, Dict, Any

from aos.core.institution.plugins.base import InstitutionPlugin


class SportsPlugin(InstitutionPlugin):
    """
    Plugin for sports-based institutions (football clubs, athletic teams, etc.).
    
    Provides:
    - Team registry management
    - Training and Match attendance tracking
    - Membership dues and equipment management
    - Tournament organization
    """
    
    @property
    def institution_type(self) -> str:
        return "sports"
    
    @property
    def display_name(self) -> str:
        return "Sports Clubs & Teams"
    
    def get_sidebar_items(self) -> List[Dict[str, Any]]:
        """Return sports-specific sidebar items."""
        return [
            {
                "text": "Fixtures",
                "href": "#",  # Placeholder until specific routes are built
                "icon": '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z">
                    </path>
                </svg>'''
            },
            {
                "text": "Results",
                "href": "#",  # Placeholder
                "icon": '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z">
                    </path>
                </svg>'''
            }
        ]
    
    def get_dashboard_widgets(self, community_id: str) -> List[Dict[str, Any]]:
        """Return sports-specific dashboard widgets."""
        return [
            {
                "type": "team_stats",
                "title": "Active Players",
                "data": {
                    "community_id": community_id,
                    "count_active": 0  # Placeholder
                }
            }
        ]
    
    def get_attendance_types(self) -> List[str]:
        """Return sports-specific attendance categories."""
        return ["Training", "Match Day", "Tournament", "General Meeting"]

    def get_financial_categories(self) -> List[str]:
        """Return sports-specific financial categories."""
        return ["Membership Dues", "Equipment", "Transport", "Tournament Entry", "Sponsorship"]
    
    def get_context_labels(self) -> Dict[str, str]:
        """Return sports-specific labels for shared features."""
        return {
            "attendance_label": "Match & Training Attendance",
            "financial_label": "Club Funds",
            "group_label": "Teams",
            "member_label": "Team Registry",
            "prayer_label": "Player Requests"
        }
