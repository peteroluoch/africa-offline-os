"""
Faith Communities Plugin

Implements faith-specific features for churches and mosques.
Includes prayer requests, worship attendance tracking, and tithes/offerings management.
"""
from __future__ import annotations

from typing import List, Dict, Any

from aos.core.institution.plugins.base import InstitutionPlugin


class FaithPlugin(InstitutionPlugin):
    """
    Plugin for faith-based institutions (churches, mosques).
    
    Provides:
    - Prayer request management
    - Worship attendance tracking
    - Tithes and offerings management
    - Ministry group organization
    """
    
    @property
    def institution_type(self) -> str:
        return "faith"
    
    @property
    def display_name(self) -> str:
        return "Faith Communities"
    
    def get_sidebar_items(self) -> List[Dict[str, Any]]:
        """Return faith-specific sidebar items."""
        return [
            {
                "text": "Prayer Requests",
                "href": "/institution/prayers/ui",
                "icon": '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z">
                    </path>
                </svg>'''
            }
        ]
    
    def get_dashboard_widgets(self, community_id: str) -> List[Dict[str, Any]]:
        """Return faith-specific dashboard widgets."""
        # Future: Add prayer stats widget
        return [
            {
                "type": "prayer_stats",
                "title": "Pending Prayer Requests",
                "data": {
                    "community_id": community_id,
                    "count_pending": 0  # Placeholder, will be populated by service
                }
            }
        ]
    
    def get_attendance_types(self) -> List[str]:
        """Return faith-specific attendance categories."""
        return ["Main Service", "Youth Service", "Mid-week", "Special Event"]

    def get_financial_categories(self) -> List[str]:
        """Return faith-specific financial categories."""
        return ["Tithe", "Offering", "Building", "Project", "Other"]
    
    def get_context_labels(self) -> Dict[str, str]:
        """Return faith-specific labels for shared features."""
        return {
            "attendance_label": "Registry Attendance",
            "financial_label": "Institutional Finances",
            "group_label": "Institutional Groups",
            "member_label": "Institutional Registry",
            "prayer_label": "Prayer & Requests"
        }
