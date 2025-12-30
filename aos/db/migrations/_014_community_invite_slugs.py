"""
Migration 013: Add invite_slug to Community Groups
Adds a human-readable slug for Telegram invite links.
"""
import sqlite3
import logging
import re

logger = logging.getLogger("aos.db.migrations")

def slugify(text: str) -> str:
    """Sanitize name into a Telegram-friendly start payload."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9_]', '_', text)
    text = re.sub(r'_+', '_', text)
    return text.strip('_')

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    try:
        # 1. Add column
        cursor.execute("ALTER TABLE community_groups ADD COLUMN invite_slug TEXT")
        logger.info("Column invite_slug added to community_groups.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.warning("Column invite_slug already exists.")
        else:
            raise e

    # 2. Backfill existing groups with unique slugs
    cursor.execute("SELECT id, name FROM community_groups")
    groups = cursor.fetchall()
    
    for group_id, name in groups:
        slug = slugify(name)
        # Check for uniqueness, append ID suffix if needed
        cursor.execute("SELECT count(*) FROM community_groups WHERE invite_slug = ?", (slug,))
        if cursor.fetchone()[0] > 0:
            slug = f"{slug}_{group_id.split('-')[-1].lower()}"
        
        cursor.execute("UPDATE community_groups SET invite_slug = ? WHERE id = ?", (slug, group_id))
        logger.info(f"Backfilled slug for {name}: {slug}")

    # 3. Create unique index
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_cg_slug ON community_groups(invite_slug)")
    
    conn.commit()
    logger.info("Migration 013 complete.")

if __name__ == "__main__":
    # Test script run
    conn = sqlite3.connect("aos.db")
    migrate(conn)
    conn.close()
