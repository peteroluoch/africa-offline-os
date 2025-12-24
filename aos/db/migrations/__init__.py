from __future__ import annotations
import sqlite3
import hashlib
from typing import List

class MigrationManager:
    """
    Manages SQLite database schema migrations.
    Favouring simplicity and robustness for edge-first deployments.
    """
    
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def ensure_migration_table(self) -> None:
        """Create the table that tracks applied migrations."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version_id INTEGER PRIMARY KEY,
                migration_hash TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def get_applied_versions(self) -> List[int]:
        """Return IDs of all applied migrations."""
        cursor = self.conn.execute("SELECT version_id FROM schema_migrations ORDER BY version_id")
        return [row[0] for row in cursor.fetchall()]

    def apply_migrations(self, migrations: List[str]) -> None:
        """
        Apply a list of SQL migrations in order.
        Skips already applied migrations based on their index.
        """
        self.ensure_migration_table()
        applied = self.get_applied_versions()
        
        for idx, sql in enumerate(migrations):
            version_id = idx + 1
            if version_id in applied:
                continue
            
            # Use hash for integrity check
            m_hash = hashlib.sha256(sql.encode()).hexdigest()
            
            try:
                # Use a single transaction per migration
                self.conn.execute("BEGIN TRANSACTION;")
                self.conn.execute(sql)
                self.conn.execute(
                    "INSERT INTO schema_migrations (version_id, migration_hash) VALUES (?, ?)",
                    (version_id, m_hash)
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise RuntimeError(f"Failed to apply migration version {version_id}: {str(e)}")
