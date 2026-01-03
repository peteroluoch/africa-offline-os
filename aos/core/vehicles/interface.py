from abc import ABC, abstractmethod
from typing import Any

class VehicleInterface(ABC):
    """
    Abstract Interface for A-OS Vehicles (Communication Channels).
    Ensures the 'Brain' remains vehicle-agnostic.
    """
    
    @abstractmethod
    async def send_message(self, to: str, message: str, metadata: dict[str, Any] | None = None) -> bool:
        """
        Send an outbound message through the vehicle.
        
        :param to: The vehicle-specific identity (e.g., chat_id for Telegram)
        :param message: The message text
        :param metadata: Optional key-value pairs for vehicle-specific features
        :return: True if sent successfully, False otherwise (triggers retry queue)
        """
        pass

    @abstractmethod
    def register_identity(self, identity: str) -> None:
        """
        Register the vehicle's own identity (e.g., bot token, shortcode).
        """
        pass

    @property
    @abstractmethod
    def vehicle_type(self) -> str:
        """Return the unique string identifier for this vehicle (e.g., 'telegram', 'sms')."""
        pass
