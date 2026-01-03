"""
Migration 021: Add institution_type support for plugin architecture.

This migration adds the `institution_type` field to enable multiple institution types
(faith, sports, political, youth, women) while maintaining backward compatibility.

All existing records default to 'faith' to preserve current functionality.
"""
import sqlite3


def up(conn: sqlite3.Connection) -> None:
    """Add institution_type field to support multiple institution types."""
    
    # Add institution_type to institution_members
    conn.execute("""
        ALTER TABLE institution_members 
        ADD COLUMN institution_type TEXT DEFAULT 'faith' NOT NULL
    """)
    
    # Add institution_type to institution_groups
    conn.execute("""
        ALTER TABLE institution_groups 
        ADD COLUMN institution_type TEXT DEFAULT 'faith' NOT NULL
    """)
    
    # Create index for efficient filtering by type
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_institution_members_type 
        ON institution_members(institution_type)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_institution_groups_type 
        ON institution_groups(institution_type)
    """)
    
    # Create index for composite filtering (community + type)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_institution_members_community_type 
        ON institution_members(community_id, institution_type)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_institution_groups_community_type 
        ON institution_groups(community_id, institution_type)
    """)
    
    conn.commit()


def down(conn: sqlite3.Connection) -> None:
    """Rollback: Remove institution_type field."""
    
    # SQLite doesn't support DROP COLUMN directly, so we need to recreate tables
    # For safety, we'll just document the rollback strategy
    # In production, use a backup before migration
    
    # Drop indexes first
    conn.execute("DROP INDEX IF EXISTS idx_institution_members_type")
    conn.execute("DROP INDEX IF EXISTS idx_institution_groups_type")
    conn.execute("DROP INDEX IF EXISTS idx_institution_members_community_type")
    conn.execute("DROP INDEX IF EXISTS idx_institution_groups_community_type")
    
    # Note: Full rollback requires table recreation with backup data
    # This is intentionally left as a manual process for data safety
    
    conn.commit()
