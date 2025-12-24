from __future__ import annotations

# List of migrations in order. 
# MigrationManager will use the list index + 1 as the version_id.
MIGRATIONS = [
    # 001: Core Kernel Tables
    """
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        public_key BLOB NOT NULL,
        alias TEXT,
        status TEXT DEFAULT 'active',
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS operators (
        id TEXT PRIMARY KEY,
        sub TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS node_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]
