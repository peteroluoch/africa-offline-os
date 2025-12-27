#!/usr/bin/env python3
"""Grant ADMIN role to operator."""
from aos.db.engine import connect
from aos.core.config import Settings

settings = Settings()
db = connect(settings.sqlite_path)

# Check roles
cursor = db.execute("SELECT id, name FROM roles")
roles = cursor.fetchall()
print("Available Roles:")
for role in roles:
    print(f"  {role[1]}: {role[0]}")

# Find ADMIN role
admin_role = [r for r in roles if 'ADMIN' in r[1].upper()]
if not admin_role:
    print("\n❌ ADMIN role not found!")
    db.close()
    exit(1)

admin_role_id = admin_role[0][0]
print(f"\n✅ ADMIN Role ID: {admin_role_id}")

# Get current operator
cursor = db.execute("SELECT id, username, role_id FROM operators LIMIT 1")
operator = cursor.fetchone()

if not operator:
    print("❌ No operators found!")
    db.close()
    exit(1)

print(f"\nCurrent Operator: {operator[1]} (Role: {operator[2]})")

# Update to ADMIN
db.execute("UPDATE operators SET role_id = ? WHERE id = ?", (admin_role_id, operator[0]))
db.commit()

print(f"✅ Granted ADMIN role to {operator[1]}")
print("\n🔄 Please log out and log back in for changes to take effect.")

db.close()
