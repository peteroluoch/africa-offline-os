import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from aos.db.migrations import registry, MigrationManager
from aos.db.engine import connect

def run_migrations():
    print("[MIGRATION] Initializing migration manager...")
    conn = connect("aos.db")
    manager = MigrationManager(conn)
    
    try:
        print("[MIGRATION] Applying all pending migrations...")
        manager.apply_migrations(registry.MIGRATIONS)
        print("[MIGRATION] All migrations applied successfully.")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        
    conn.close()

if __name__ == "__main__":
    run_migrations()

if __name__ == "__main__":
    run_migrations()
