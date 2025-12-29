import sqlite3
import uuid
from datetime import UTC, datetime
from aos.core.security.password import get_password_hash

def create_operator(username, password, role_name, community_id=None):
    conn = sqlite3.connect("aos.db")
    cursor = conn.cursor()
    
    # Get Role ID
    cursor.execute("SELECT id FROM roles WHERE name=?", (role_name,))
    role_row = cursor.fetchone()
    if not role_row:
        print(f"❌ Role '{role_name}' not found.")
        return
    role_id = role_row[0]
    
    # Create Operator
    op_id = str(uuid.uuid4())
    pw_hash = get_password_hash(password)
    
    try:
        cursor.execute(
            "INSERT INTO operators (id, username, password_hash, role_id, created_at, community_id) VALUES (?, ?, ?, ?, ?, ?)",
            (op_id, username, pw_hash, role_id, datetime.now(UTC).isoformat(), community_id)
        )
        conn.commit()
        print(f"✅ Created {role_name}: '{username}' (Password: {password})")
        if community_id:
            print(f"   Mapped to Community: {community_id}")
    except sqlite3.IntegrityError:
        print(f"⚠️ User '{username}' already exists.")
    finally:
        conn.close()

# --- SETUP TEST ACCOUNTS ---
# 1. Get a test group ID
conn = sqlite3.connect("aos.db")
group = conn.execute("SELECT id, name FROM community_groups LIMIT 1").fetchone()
conn.close()

if group:
    group_id, group_name = group
    # A. Church Admin (Isolated to one group)
    create_operator("church_admin", "church123", "community_admin", group_id)
    
    # B. Field Agent (Operator - typically for data entry)
    create_operator("field_agent", "agent123", "operator", group_id)
else:
    print("❌ No community groups found to map to.")
