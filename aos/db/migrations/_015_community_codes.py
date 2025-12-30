"""
Migration 015: Add Community Code Support
Enables self-registration via human-readable community codes.
"""
import sqlite3
import logging

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    try:
        # Add community_code column
        cursor.execute("ALTER TABLE community_groups ADD COLUMN community_code TEXT")
        logger.info("Column community_code added to community_groups.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.warning("Column community_code already exists.")
        else:
            raise e

    try:
        # Add code_active column
        cursor.execute("ALTER TABLE community_groups ADD COLUMN code_active BOOLEAN DEFAULT 0")
        logger.info("Column code_active added to community_groups.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.warning("Column code_active already exists.")
        else:
            raise e

    # Create unique index for active codes only
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_cg_active_code 
            ON community_groups(community_code) 
            WHERE code_active = 1 AND community_code IS NOT NULL
        """)
        logger.info("Unique index created for active community codes.")
    except sqlite3.OperationalError as e:
        logger.warning(f"Index creation skipped: {e}")

    conn.commit()
    logger.info("Migration 015 complete.")
