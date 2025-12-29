"""
Migration 010: Broadcast Tables
Creates tables for community broadcasting, audit logs, and delivery tracking.
Includes idempotency keys and lease-based locking for worker safety.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Broadcasts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broadcasts (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        message TEXT NOT NULL,
        channels TEXT NOT NULL,  -- JSON array
        status TEXT NOT NULL DEFAULT 'draft',
        idempotency_key TEXT UNIQUE,
        scheduled_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        locked_at DATETIME,
        lock_owner TEXT,
        sent_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        FOREIGN KEY (community_id) REFERENCES community_groups(id)
    )
    """)

    # Broadcast Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broadcast_audit_logs (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL, -- 'create', 'approve', 'send', 'cancel', 'retry'
        broadcast_id TEXT NOT NULL,
        metadata TEXT, -- JSON
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id)
    )
    """)

    # Broadcast Deliveries (Tracking each recipient)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broadcast_deliveries (
        id TEXT PRIMARY KEY,
        broadcast_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        error TEXT,
        sent_at DATETIME,
        FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id),
        FOREIGN KEY (member_id) REFERENCES community_members(id)
    )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_b_status ON broadcasts(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_b_community ON broadcasts(community_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bd_broadcast ON broadcast_deliveries(broadcast_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bd_status ON broadcast_deliveries(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bal_broadcast ON broadcast_audit_logs(broadcast_id)")

    conn.commit()
    logger.info("Migration 010: Broadcast tables created successfully.")
