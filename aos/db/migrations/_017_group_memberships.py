"""
Migration 017: Institutional Group Memberships.
Enables members to belong to multiple subgroups (Choir, Youth, Women, etc.).
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Many-to-Many mapping for Institutional Groups
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institution_group_members (
        id TEXT PRIMARY KEY, -- Mapping UUID
        group_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES institution_groups (id),
        FOREIGN KEY (member_id) REFERENCES institution_members (id),
        UNIQUE(group_id, member_id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_igm_group ON institution_group_members(group_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_igm_member ON institution_group_members(member_id)")

    conn.commit()
    logger.info("Migration 017: Institutional group membership table created.")
