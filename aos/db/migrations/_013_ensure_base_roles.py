import json
import sqlite3
from datetime import UTC, datetime
import uuid

def apply(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # 1. Ensure 'operator' role exists
    check = cursor.execute("SELECT id FROM roles WHERE name='operator'").fetchone()
    if not check:
        role_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO roles (id, name, permissions, created_at) VALUES (?, ?, ?, ?)",
            (
                role_id, 
                "operator", 
                json.dumps(["community:view", "member:view"]), 
                datetime.now(UTC).isoformat()
            )
        )
        print(f"[Migration] 'operator' role created with ID: {role_id}")

    # 2. Ensure 'viewer' role exists
    check = cursor.execute("SELECT id FROM roles WHERE name='viewer'").fetchone()
    if not check:
        role_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO roles (id, name, permissions, created_at) VALUES (?, ?, ?, ?)",
            (
                role_id, 
                "viewer", 
                json.dumps(["view_only"]), 
                datetime.now(UTC).isoformat()
            )
        )
        print(f"[Migration] 'viewer' role created with ID: {role_id}")
    
    conn.commit()
