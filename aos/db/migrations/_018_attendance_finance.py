"""
Migration 018: Attendance and Finance Ledger.
Adds support for institutional attendance tracking and sovereign financial logging.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Attendance Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutional_attendance (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        service_date DATETIME NOT NULL,
        service_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'present',
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (community_id) REFERENCES community_groups (id),
        FOREIGN KEY (member_id) REFERENCES institution_members (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ia_community_date ON institutional_attendance(community_id, service_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ia_member ON institutional_attendance(member_id)")

    # Financial Ledger Table (Giving, Tithes, Pledges)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutional_finances (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        member_id TEXT,
        amount REAL NOT NULL,
        category TEXT NOT NULL, -- tithe, offering, pledge
        is_pledge BOOLEAN DEFAULT 0,
        entry_date DATETIME NOT NULL,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (community_id) REFERENCES community_groups (id),
        FOREIGN KEY (member_id) REFERENCES institution_members (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_if_community_cat ON institutional_finances(community_id, category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_if_member ON institutional_finances(member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_if_date ON institutional_finances(entry_date)")

    conn.commit()
    logger.info("Migration 018: Attendance and Financial tables created.")
