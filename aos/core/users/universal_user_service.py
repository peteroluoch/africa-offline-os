"""
Universal User Service
Manages unified user registration and role-based access across all modules.
Follows FAANG standards and 01_roles.md principles.
"""
import json
import logging
import sqlite3
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)

class UniversalUserService:
    """
    Universal user management service.
    Single source of truth for all user data across modules.
    """

    VALID_ROLES = ["farmer", "driver", "passenger", "buyer", "operator"]

    def __init__(self, db_path: str = "aos.db"):
        self.db_path = db_path

    def register_user(
        self,
        chat_id: int,
        phone: str,
        name: str,
        town: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Register a new user.
        
        Args:
            chat_id: Telegram chat ID
            phone: User phone number (unique identifier)
            name: User full name
            town: User town/location
            roles: List of roles (farmer, driver, etc.)
        
        Returns:
            User dict if successful, None otherwise
        """
        try:
            # Validate roles
            if roles:
                invalid_roles = [r for r in roles if r not in self.VALID_ROLES]
                if invalid_roles:
                    logger.error(f"Invalid roles: {invalid_roles}")
                    return None

            roles_json = json.dumps(roles or [])

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO telegram_users (chat_id, phone, name, town, roles)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, phone, name, town, roles_json))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Registered user {user_id}: {name} ({phone})")

            return self.get_user_by_chat_id(chat_id)

        except sqlite3.IntegrityError as e:
            logger.error(f"User already exists: {e}")
            return None
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None

    def get_user_by_chat_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram chat ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM telegram_users WHERE chat_id = ?
            """, (chat_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                user = dict(row)
                user['roles'] = json.loads(user['roles'])
                return user

            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM telegram_users WHERE phone = ?
            """, (phone,))

            row = cursor.fetchone()
            conn.close()

            if row:
                user = dict(row)
                user['roles'] = json.loads(user['roles'])
                return user

            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def add_role(self, chat_id: int, role: str) -> bool:
        """Add role to user."""
        if role not in self.VALID_ROLES:
            logger.error(f"Invalid role: {role}")
            return False

        try:
            user = self.get_user_by_chat_id(chat_id)
            if not user:
                return False

            roles = user['roles']
            if role not in roles:
                roles.append(role)

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE telegram_users 
                    SET roles = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                """, (json.dumps(roles), chat_id))

                conn.commit()
                conn.close()

                logger.info(f"Added role {role} to user {chat_id}")

            return True
        except Exception as e:
            logger.error(f"Error adding role: {e}")
            return False

    def remove_role(self, chat_id: int, role: str) -> bool:
        """Remove role from user."""
        try:
            user = self.get_user_by_chat_id(chat_id)
            if not user:
                return False

            roles = user['roles']
            if role in roles:
                roles.remove(role)

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE telegram_users 
                    SET roles = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                """, (json.dumps(roles), chat_id))

                conn.commit()
                conn.close()

                logger.info(f"Removed role {role} from user {chat_id}")

            return True
        except Exception as e:
            logger.error(f"Error removing role: {e}")
            return False

    def has_role(self, chat_id: int, role: str) -> bool:
        """Check if user has specific role."""
        user = self.get_user_by_chat_id(chat_id)
        if not user:
            return False
        return role in user['roles']

    def set_active_domain(self, chat_id: int, domain: str) -> bool:
        """Set the current active domain for a user."""
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE telegram_users 
                    SET active_domain = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                """, (domain, chat_id))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Set active domain to {domain} for user {chat_id}")
                return True
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                logger.error(f"Error setting active domain: {e}")
                return False
            except Exception as e:
                logger.error(f"Error setting active domain: {e}")
                return False
        return False

    def get_active_domain(self, chat_id: int) -> Optional[str]:
        """Get the current active domain for a user."""
        user = self.get_user_by_chat_id(chat_id)
        return user.get("active_domain") if user else None

    def update_user(
        self,
        chat_id: int,
        name: Optional[str] = None,
        town: Optional[str] = None
    ) -> bool:
        """Update user information."""
        try:
            updates = []
            params = []

            if name:
                updates.append("name = ?")
                params.append(name)

            if town:
                updates.append("town = ?")
                params.append(town)

            if not updates:
                return True

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(chat_id)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f"""
                UPDATE telegram_users 
                SET {', '.join(updates)}
                WHERE chat_id = ?
            """, params)

            conn.commit()
            conn.close()

            logger.info(f"Updated user {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
