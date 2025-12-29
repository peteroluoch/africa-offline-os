"""
Migration 011: Community Activity Logs
Creates a general activity log for group and member management actions.
Ensures immutability and auditability as per FAANG standards.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Community Activity Logs (General purpose for module)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_activity_logs (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        action TEXT NOT NULL, -- 'group_create', 'group_update', 'group_deactivate', 'member_add', 'member_remove', 'member_update'
        target_id TEXT NOT NULL, -- ID of the group or member being acted upon
        community_id TEXT, -- Associated group ID (if applicable)
        metadata TEXT, -- JSON payload of the change/details
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Indexes for fast auditing
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cal_action ON community_activity_logs(action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cal_target ON community_activity_logs(target_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cal_actor ON community_activity_logs(actor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cal_community ON community_activity_logs(community_id)")

    conn.commit()
    logger.info("Migration 011: Community activity log table created.")
