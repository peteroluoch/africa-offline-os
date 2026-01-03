"""
Migration: Create message_retry_queue table.
Ensures outbound messages are never lost due to vehicle connectivity issues.
"""
import sqlite3

def up(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # 1. Message Retry Queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_retry_queue (
            id TEXT PRIMARY KEY,
            community_id TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            vehicle_identity TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,            -- JSON metadata
            retry_count INTEGER DEFAULT 0,
            next_retry_at DATETIMEDEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (community_id) REFERENCES communities(id)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_retry_next ON message_retry_queue(next_retry_at)")
    
    conn.commit()

def down(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS message_retry_queue")
    conn.commit()
