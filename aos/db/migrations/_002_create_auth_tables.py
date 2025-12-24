import sqlite3
import uuid
import json
from datetime import datetime, timezone
from aos.core.security.password import get_password_hash

def apply(conn: sqlite3.Connection) -> None:
    # Use cursor for consistency
    cursor = conn.cursor()
    
    # 1. Create Roles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        permissions TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 2. Create Operators
    # Ensure no collision if table exists but has wrong schema (dev safety)
    try:
        cursor.execute("SELECT username FROM operators LIMIT 1")
    except sqlite3.OperationalError:
        # Table might exist but missing username, or not exist at all
        cursor.execute("DROP TABLE IF EXISTS operators")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operators (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT,
        FOREIGN KEY(role_id) REFERENCES roles(id)
    )
    """)
    
    # 3. Bootstrap Admin
    # Check if admin role exists
    check = cursor.execute("SELECT id FROM roles WHERE name='admin'").fetchone()
    if not check:
        role_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        
        # Create Admin Role
        cursor.execute(
            "INSERT INTO roles (id, name, permissions, created_at) VALUES (?, ?, ?, ?)",
            (role_id, "admin", json.dumps(["*"]), datetime.now(timezone.utc).isoformat())
        )
        
        # Create Root Operator (admin / aos_root_2025)
        pw_hash = get_password_hash("aos_root_2025")
        cursor.execute(
            "INSERT INTO operators (id, username, password_hash, role_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (admin_id, "admin", pw_hash, role_id, datetime.now(timezone.utc).isoformat())
        )
        print("[Migration] Hardened 'admin' operator bootstrapped.")
    
    conn.commit()
