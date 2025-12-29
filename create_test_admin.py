import sqlite3
import os
import uuid
from datetime import UTC, datetime
from aos.core.security.password import get_password_hash

db_path = "aos.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Get role ID for community_admin
    cursor.execute("SELECT id FROM roles WHERE name='community_admin'")
    role_id = cursor.fetchone()[0]
    
    # 2. Create operator
    username = "comm_admin"
    password = "password123"
    pw_hash = get_password_hash(password)
    op_id = str(uuid.uuid4())
    group_id = "GRP-D1E4CF71"
    
    # Check if exists
    cursor.execute("SELECT id FROM operators WHERE username=?", (username,))
    if cursor.fetchone():
        print(f"Operator {username} already exists.")
    else:
        cursor.execute(
            "INSERT INTO operators (id, username, password_hash, role_id, created_at, community_id) VALUES (?, ?, ?, ?, ?, ?)",
            (op_id, username, pw_hash, role_id, datetime.now(UTC).isoformat(), group_id)
        )
        print(f"Community Admin '{username}' created for group '{group_id}'.")
    
    conn.commit()
    conn.close()
