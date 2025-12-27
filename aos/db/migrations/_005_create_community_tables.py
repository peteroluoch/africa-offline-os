"""
Migration 005: Create Community Tables.
Defines tables for groups, events, announcements and inquiry caching.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Community Groups Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_groups (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        group_type TEXT,
        tags TEXT DEFAULT '[]', -- JSON list
        location TEXT,
        admin_id TEXT,
        trust_level TEXT DEFAULT 'local',
        preferred_channels TEXT DEFAULT 'ussd,sms',
        active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cg_location ON community_groups(location)")

    # Community Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_events (
        id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        title TEXT NOT NULL,
        event_type TEXT,
        start_time DATETIME NOT NULL,
        end_time DATETIME,
        recurrence TEXT,
        visibility TEXT DEFAULT 'public',
        language TEXT DEFAULT 'en',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES community_groups (id)
    )
    """)

    # Community Announcements Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_announcements (
        id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        message TEXT NOT NULL,
        urgency TEXT DEFAULT 'normal',
        expires_at DATETIME,
        target_audience TEXT DEFAULT 'public',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES community_groups (id)
    )
    """)

    # Community Inquiry Cache Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_inquiry_cache (
        id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        normalized_question TEXT NOT NULL,
        answer TEXT NOT NULL,
        hit_count INTEGER DEFAULT 0,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES community_groups (id)
    )
    """)

    conn.commit()
    logger.info("Migration 005: Community tables created.")
