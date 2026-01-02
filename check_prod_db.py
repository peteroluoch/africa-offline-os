import sqlite3
conn = sqlite3.connect("aos.db")
cursor = conn.execute("PRAGMA table_info(community_groups)")
cols = [row[1] for row in cursor.fetchall()]
print("Columns:", cols)
print("Has community_code:", "community_code" in cols)
print("Has code_active:", "code_active" in cols)

if "community_code" in cols:
    cursor = conn.execute("SELECT id, name, community_code, code_active FROM community_groups WHERE community_code IS NOT NULL")
    for row in cursor.fetchall():
        print(f"\nCommunity: {row[1]}")
        print(f"  Code: {row[2]}")
        print(f"  Active: {row[3]}")
conn.close()
