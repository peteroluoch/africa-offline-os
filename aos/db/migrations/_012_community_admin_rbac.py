import json
import sqlite3
from datetime import UTC, datetime
import uuid

def apply(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # 1. Add community_id to operators
    # SQLite doesn't support ADD COLUMN with FOREIGN KEY directly in some versions,
    # but we can add the column and then enforce it in logic.
    try:
        cursor.execute("ALTER TABLE operators ADD COLUMN community_id TEXT")
    except sqlite3.OperationalError:
        # Column might already exist
        pass

    # 2. Add community_admin role
    check = cursor.execute("SELECT id FROM roles WHERE name='community_admin'").fetchone()
    if not check:
        role_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO roles (id, name, permissions, created_at) VALUES (?, ?, ?, ?)",
            (
                role_id, 
                "community_admin", 
                json.dumps(["community:manage", "broadcast:send"]), 
                datetime.now(UTC).isoformat()
            )
        )
        print(f"[Migration] 'community_admin' role created with ID: {role_id}")

    # 3. Ensure 'root' role exists (Super Admin)
    check = cursor.execute("SELECT id FROM roles WHERE name='root'").fetchone()
    if not check:
        # Check if 'admin' exists and maybe rename it? 
        # Actually, let's just create 'root' as the top-level.
        # But wait, existing logic uses 'admin' from _002.
        # PM said super_admin | community_admin.
        # Let's create 'super_admin' role.
        role_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO roles (id, name, permissions, created_at) VALUES (?, ?, ?, ?)",
            (
                role_id, 
                "super_admin", 
                json.dumps(["*"]), 
                datetime.now(UTC).isoformat()
            )
        )
        print(f"[Migration] 'super_admin' role created with ID: {role_id}")
    
    conn.commit()
