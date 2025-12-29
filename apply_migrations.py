import sqlite3
import os
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS

db_path = "aos.db"
if os.path.exists(db_path):
    print(f"Applying migrations to {db_path}...")
    conn = sqlite3.connect(db_path)
    try:
        mgr = MigrationManager(conn)
        mgr.apply_migrations(MIGRATIONS)
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
