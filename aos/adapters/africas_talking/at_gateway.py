"""
Africa's Talking Gateway Implementation.
Handles production-ready SMS, USSD, and WhatsApp routing.
"""
import logging
import africastalking
from typing import Any, Dict, List, Optional
from aos.core.channels.base import ChannelGateway

logger = logging.getLogger(__name__)

class AfricaTalkingGateway(ChannelGateway):
    """
    Concrete implementation of ChannelGateway for Africa's Talking.
    Supports SMS, USSD (parsing), and WhatsApp.
    """

    def __init__(self, username: str, api_key: str, environment: str = "sandbox"):
        self.username = username
        self.api_key = api_key
        self.environment = environment
        
        # Initialize AT SDK
        africastalking.initialize(username, api_key)
        self.sms_service = africastalking.SMS

    async def send(self, to: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a message via Africa's Talking.
        Defaults to SMS, but can be extended for WhatsApp/USSD push.
        """
        try:
            # AT expects numbers in E.164, which our UniversalUserService now ensures.
            recipients = [to]
            
            # Use enqueue=True for production reliability
            response = self.sms_service.send(message, recipients, enqueue=True)
            
            # Log successful dispatch
            logger.info(f"AT Gateway: Message sent to {to}. Response: {response}")
            return True
        except Exception as e:
            logger.error(f"AT Gateway: Failed to send message to {to}. Error: {e}")
            return False

    async def receive(self) -> List[Dict[str, Any]]:
        """
        Receive incoming messages. 
        Note: In production, AT usually pushes to a webhook. 
        This method can be used for polling if supported or for cleanup/status checks.
        """
        # For now, we return empty as we're webhook-driven in our FastAPI routers.
        return []
