"""
Migration 009: Community Members Table
Creates the community_members table to associate users with communities.
Enables strict message isolation enforcement at the kernel level.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Community Members Table
    # SECURITY: This table is the ONLY source of truth for community membership
    # Recipient resolution MUST use: WHERE community_id = ?
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_members (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        active BOOLEAN DEFAULT 1,
        FOREIGN KEY (community_id) REFERENCES community_groups(id),
        UNIQUE(community_id, user_id, channel)
    )
    """)
    
    # Index for fast community→members lookup (critical for message delivery)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cm_community 
        ON community_members(community_id)
    """)
    
    # Index for fast user→communities lookup
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cm_user 
        ON community_members(user_id)
    """)
    
    # Index for active members only
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cm_active 
        ON community_members(community_id, active)
    """)

    conn.commit()
    logger.info("Migration 009: Community members table created with isolation indexes.")
