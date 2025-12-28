"""
Base Domain Class
Blueprint for all A-OS domains (Agri, Transport, Health, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseDomain(ABC):
    """Abstract base class for all A-OS domains."""
    
    def __init__(self, adapter):
        self.adapter = adapter
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Domain name (e.g., 'agriculture')"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human readable name (e.g., '🌾 Agriculture')"""
        pass
    
    @abstractmethod
    def get_commands(self) -> List[Dict[str, str]]:
        """List of commands supported by this domain."""
        pass
    
    @abstractmethod
    async def handle_command(self, chat_id: int, command: str, args: List[str]) -> bool:
        """Handle a text command within this domain."""
        pass
    
    @abstractmethod
    async def handle_callback(self, chat_id: int, callback_data: str) -> bool:
        """Handle a callback from this domain's interactive elements."""
        pass
