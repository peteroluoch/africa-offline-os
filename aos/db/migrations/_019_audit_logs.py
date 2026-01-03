"""
Migration: Create institution_audit_logs table.
Ensures every administrative action is recorded in an append-only log.
"""
import sqlite3

def up(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # 1. Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS institution_audit_logs (
            id TEXT PRIMARY KEY,
            community_id TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            action_type TEXT NOT NULL, -- e.g., 'MEMBER_JOIN', 'FINANCE_LOG', 'BROADCAST'
            target_id TEXT,             -- ID of the entity affected
            details TEXT,              -- JSON or string details
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (community_id) REFERENCES communities(id)
        )
    """)
    
    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_community ON institution_audit_logs(community_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON institution_audit_logs(timestamp)")
    
    conn.commit()

def down(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS institution_audit_logs")
    conn.commit()
