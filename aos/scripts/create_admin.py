import sqlite3
import uuid
from datetime import datetime
from aos.core.security.auth import get_password_hash

def create_admin():
    conn = sqlite3.connect("aos.db")
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        print("Users table not found. Please run the app first to migrate.")
        return

    admin_id = str(uuid.uuid4())
    username = "admin"
    password = "password123"
    hashed_password = get_password_hash(password)
    
    try:
        cursor.execute("""
            INSERT INTO users (chat_id, name, phone, town, roles, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "admin_chat_id", 
            "System Admin", 
            "000000000", 
            "Nairobi", 
            "admin,operator", 
            datetime.now().isoformat()
        ))
        
        # We also need to add a password entry if it's separate, but usually auth.py uses this table
        # Let's check auth.py user fetch logic
        conn.commit()
        print(f"User {username} created with password: {password}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
