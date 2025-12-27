"""
Database migration: Domain-aware user system
Renames 'village' to 'town' and adds 'active_domain' column.
"""

def upgrade(conn):
    """Update telegram_users table."""
    cursor = conn.cursor()
    
    # 1. Rename 'village' to 'town'
    # Check if 'village' exists before trying to rename (for idempotency)
    cursor.execute("PRAGMA table_info(telegram_users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'village' in columns and 'town' not in columns:
        cursor.execute("ALTER TABLE telegram_users RENAME COLUMN village TO town")
        print("✅ Renamed 'village' to 'town'")
    elif 'town' in columns:
        print("ℹ️ Column 'town' already exists")
    
    # 2. Add 'active_domain' column
    if 'active_domain' not in columns:
        cursor.execute("ALTER TABLE telegram_users ADD COLUMN active_domain TEXT")
        print("✅ Added 'active_domain' column")
    else:
        print("ℹ️ Column 'active_domain' already exists")
    
    conn.commit()

def downgrade(conn):
    """Revert changes."""
    cursor = conn.cursor()
    # Note: SQLite doesn't easily support dropping columns or renaming them back without careful checking
    # For this project, we'll implement a simple rename back if possible
    cursor.execute("PRAGMA table_info(telegram_users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'town' in columns:
        cursor.execute("ALTER TABLE telegram_users RENAME COLUMN town TO village")
        print("✅ Renamed 'town' back to 'village'")
        
    # Standard SQLite doesn't support DROP COLUMN until very recent versions.
    # We will leave active_domain if dropping is not critical for downgrade.
    
    conn.commit()

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect("aos.db")
    upgrade(conn)
    conn.close()
