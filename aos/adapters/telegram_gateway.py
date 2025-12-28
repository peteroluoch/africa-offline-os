"""
Telegram API Gateway Implementation.
Isolates network logic from the Adapter.
"""
import os
import requests
import logging
from typing import Any, Dict, List, Optional
from aos.core.channels.base import ChannelGateway

logger = logging.getLogger(__name__)

class TelegramGateway(ChannelGateway):
    """
    Concrete implementation of ChannelGateway for Telegram.
    Handles raw HTTPS requests to the Telegram Bot API.
    """

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send a message via Telegram API.
        'to' is the chat_id.
        """
        if not self.bot_token:
            logger.error("Telegram Gateway: BOT_TOKEN missing")
            return {"ok": False, "error": "token_missing"}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": to,
            "text": message,
            "parse_mode": "HTML"
        }
        
        # Merge metadata (like reply_markup) if provided
        metadata = kwargs.get("metadata") or {}
        if "reply_markup" in metadata:
            payload["reply_markup"] = metadata["reply_markup"]

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Telegram Gateway Error: {e}")
            return {"ok": False, "error": str(e)}

    async def get_updates(self, offset: int = 0, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieve updates from Telegram via long polling.
        """
        if not self.bot_token: return []
        
        url = f"{self.base_url}/getUpdates"
        payload = {
            'offset': offset,
            'timeout': timeout,
            'allowed_updates': ['message', 'callback_query']
        }
        
        try:
            # Using block-style requests for polling is acceptable here as it's run in a separate loop/thread
            response = requests.post(url, json=payload, timeout=timeout + 5)
            result = response.json()
            if result.get("ok"):
                return result.get("result", [])
            return []
        except:
            return []

    async def get_delivery_status(self, message_id: str) -> str:
        """Telegram does not provide simple status for bot messages via this API."""
        return "sent"

    def send_chat_action(self, chat_id: str, action: str = "typing") -> bool:
        """Helper for chat actions."""
        if not self.bot_token: return False
        url = f"{self.base_url}/sendChatAction"
        try:
             res = requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
             return res.json().get("ok", False)
        except:
             return False
