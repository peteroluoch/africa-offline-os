"""
Base Plugin Interface for Institution Types

Defines the contract that all institution-type plugins must implement.
This enables polymorphic behavior while maintaining type safety.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class InstitutionPlugin(ABC):
    """
    Base class for institution-type-specific features.
    
    Each institution type (faith, sports, political, youth, women) implements
    this interface to provide custom menu items, dashboard widgets, and features.
    
    FAANG Pattern: Strategy Pattern for polymorphic behavior
    """
    
    @property
    @abstractmethod
    def institution_type(self) -> str:
        """
        Return the institution type this plugin handles.
        
        Valid types: 'faith', 'sports', 'political', 'youth', 'women'
        """
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return human-readable name for this institution type."""
        pass
    
    @abstractmethod
    def get_sidebar_items(self) -> List[Dict[str, Any]]:
        """
        Return type-specific sidebar menu items.
        
        Returns:
            List of menu item dictionaries with keys:
            - text: Display text
            - href: Route path
            - icon: SVG icon markup
            - active: Boolean (optional)
        
        Example:
            [
                {
                    "text": "Prayer Requests",
                    "href": "/institution/prayers/ui",
                    "icon": "<svg>...</svg>"
                }
            ]
        """
        pass
    
    @abstractmethod
    def get_dashboard_widgets(self, community_id: str) -> List[Dict[str, Any]]:
        """
        Return type-specific dashboard widgets.
        
        Args:
            community_id: The community to fetch widget data for
        
        Returns:
            List of widget dictionaries with keys:
            - type: Widget type identifier
            - title: Widget title
            - data: Widget-specific data
        """
        pass
    
    def get_context_labels(self) -> Dict[str, str]:
        """
        Return type-specific labels for shared features.
        
        Allows customization of generic terms based on institution type.
        
        Returns:
            Dictionary mapping generic terms to type-specific terms:
            - attendance_label: "Worship Attendance" vs "Training Attendance"
            - financial_label: "Tithes & Offerings" vs "Membership Fees"
            - group_label: "Ministry Groups" vs "Teams"
        
        Example:
            {
                "attendance_label": "Worship Attendance",
                "financial_label": "Tithes & Offerings",
                "group_label": "Ministry Groups"
            }
        """
        return {
            "attendance_label": "Attendance",
            "financial_label": "Finances",
            "group_label": "Groups"
        }
