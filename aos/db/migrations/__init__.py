from __future__ import annotations

import hashlib
import sqlite3
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

    def get_applied_versions(self) -> list[int]:
        """Return IDs of all applied migrations."""
        cursor = self.conn.execute("SELECT version_id FROM schema_migrations ORDER BY version_id")
        return [row[0] for row in cursor.fetchall()]

    def apply_migrations(self, migrations: list[Any]) -> None:
        """
        Apply a list of migrations (SQL strings or Python modules).
        Skips already applied versions.
        """
        self.ensure_migration_table()
        applied = self.get_applied_versions()

        for idx, migration in enumerate(migrations):
            version_id = idx + 1
            if version_id in applied:
                continue

            # Determine content for hashing
            if hasattr(migration, 'apply'):
                # Use module name as content for hashing - more stable than str(module)
                content = getattr(migration, '__name__', str(migration))
            else:
                # SQL String
                content = str(migration)

            m_hash = hashlib.sha256(content.encode()).hexdigest()

            try:
                # Use a single transaction per migration
                # Note: Some Python migrations might manage their own transactions?
                # For safety, we wrap in BEGIN/COMMIT if it's SQL,
                # but for Python apply(conn), we pass the connection.
                # Ideally, we let the manager handle the transaction scope.

                # We can't nest transactions easily in sqlite without savepoints.
                # Let's simple assume one transaction block.

                if hasattr(migration, 'apply'):
                    migration.apply(self.conn)
                elif hasattr(migration, 'upgrade'):
                    migration.upgrade(self.conn)
                elif hasattr(migration, 'up'):
                    migration.up(self.conn)
                elif hasattr(migration, 'migrate'):
                    migration.migrate(self.conn)
                elif isinstance(migration, str):
                    self.conn.execute(migration)
                else:
                    raise TypeError(f"Migration version {version_id} is not an applicable type: {type(migration)}")

                self.conn.execute(
                    "INSERT INTO schema_migrations (version_id, migration_hash) VALUES (?, ?)",
                    (version_id, m_hash)
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise RuntimeError(f"Failed to apply migration version {version_id}: {str(e)}")
