"""
Emergency fix: Create telegram_users table in production
Run this if migration didn't apply properly
"""
import sqlite3
import os

# Production database path
DB_PATH = os.getenv("AOS_SQLITE_PATH", "/data/aos.db")

def fix_telegram_users_table():
    """Create telegram_users table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='telegram_users'
    """)
    
    if cursor.fetchone():
        print("✅ telegram_users table already exists")
        conn.close()
        return
    
    print("Creating telegram_users table...")
    
    # Create table
    cursor.execute("""
        CREATE TABLE telegram_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            village TEXT,
            roles TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX idx_telegram_users_phone 
        ON telegram_users(phone)
    """)
    
    cursor.execute("""
        CREATE INDEX idx_telegram_users_chat_id 
        ON telegram_users(chat_id)
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Created telegram_users table with indexes")
    print(f"✅ Database: {DB_PATH}")

if __name__ == "__main__":
    fix_telegram_users_table()
