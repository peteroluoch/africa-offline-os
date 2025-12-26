"""
Telegram User State Manager
Manages conversation state for Telegram users.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

class TelegramStateManager:
    """Manages user conversation state for Telegram bot."""
    
    def __init__(self, db_path: str = "aos.db"):
        self.db_path = db_path
        self._ensure_table()
    
    def _ensure_table(self):
        """Create telegram_state table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_state (
                    chat_id INTEGER PRIMARY KEY,
                    state TEXT NOT NULL,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating telegram_state table: {e}")
    
    def set_state(self, chat_id: int, state: str, data: Optional[Dict[str, Any]] = None):
        """Set user state."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_json = json.dumps(data) if data else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO telegram_state (chat_id, state, data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (chat_id, state, data_json))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error setting state: {e}")
    
    def get_state(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get user state."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT state, data FROM telegram_state WHERE chat_id = ?
            """, (chat_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                state, data_json = row
                data = json.loads(data_json) if data_json else {}
                return {"state": state, "data": data}
            
            return None
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            return None
    
    def clear_state(self, chat_id: int):
        """Clear user state."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM telegram_state WHERE chat_id = ?", (chat_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error clearing state: {e}")
