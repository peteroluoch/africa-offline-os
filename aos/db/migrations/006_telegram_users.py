"""
Database migration: Universal user system
Creates telegram_users table for unified user management across all modules.
"""

def upgrade(conn):
    """Create telegram_users table."""
    cursor = conn.cursor()

    # Create telegram_users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telegram_users (
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

    # Create index on phone for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_telegram_users_phone 
        ON telegram_users(phone)
    """)

    # Create index on chat_id for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_telegram_users_chat_id 
        ON telegram_users(chat_id)
    """)

    conn.commit()
    print("✅ Created telegram_users table with indexes")

def downgrade(conn):
    """Drop telegram_users table."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS telegram_users")
    cursor.execute("DROP INDEX IF EXISTS idx_telegram_users_phone")
    cursor.execute("DROP INDEX IF EXISTS idx_telegram_users_chat_id")
    conn.commit()
    print("✅ Dropped telegram_users table")

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect("aos.db")
    upgrade(conn)
    conn.close()
