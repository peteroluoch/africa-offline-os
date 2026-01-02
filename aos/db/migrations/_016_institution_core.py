"""
Migration 016: Institutional Core Tables.
Defines tables for institution members, groups, vehicle mapping, message logs, and prayer requests.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Institution Members Table (Institutional identity)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institution_members (
        id TEXT PRIMARY KEY, -- Member UUID
        community_id TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role_id TEXT DEFAULT 'MEMBER', -- ADMIN, SECRETARY, TREASURER, MEMBER
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        active BOOLEAN DEFAULT 1,
        FOREIGN KEY (community_id) REFERENCES community_groups (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_im_community ON institution_members(community_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_im_role ON institution_members(role_id)")

    # Institution Groups Table (Internal subgroups)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institution_groups (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (community_id) REFERENCES community_groups (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ig_community ON institution_groups(community_id)")

    # Member Vehicle Mapping (Separating Brain from Vehicle)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS member_vehicle_maps (
        id TEXT PRIMARY KEY,
        member_id TEXT NOT NULL,
        vehicle_type TEXT NOT NULL, -- 'telegram', 'sms', 'whatsapp'
        vehicle_identity TEXT NOT NULL, -- e.g. Telegram User ID
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES institution_members (id),
        UNIQUE(vehicle_type, vehicle_identity)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mvm_member ON member_vehicle_maps(member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mvm_identity ON member_vehicle_maps(vehicle_type, vehicle_identity)")

    # Institution Message Logs (Outgoing log)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institution_message_logs (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        recipient_type TEXT NOT NULL, -- 'individual', 'group', 'broadcast'
        recipient_id TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        message_type TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (community_id) REFERENCES community_groups (id),
        FOREIGN KEY (sender_id) REFERENCES institution_members (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_iml_community ON institution_message_logs(community_id)")

    # Prayer Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prayer_requests (
        id TEXT PRIMARY KEY,
        community_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        request_text TEXT NOT NULL,
        is_anonymous BOOLEAN DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (community_id) REFERENCES community_groups (id),
        FOREIGN KEY (member_id) REFERENCES institution_members (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pr_community ON prayer_requests(community_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pr_member ON prayer_requests(member_id)")

    conn.commit()
    logger.info("Migration 016: Institutional core tables created.")
