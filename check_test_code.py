import sqlite3

conn = sqlite3.connect("aos.db")
cursor = conn.execute("SELECT id, name, community_code, code_active FROM community_groups WHERE community_code = 'TEST_CODE'")
rows = cursor.fetchall()

print("Communities with TEST_CODE:")
for row in rows:
    print(f"  {row[1]} ({row[0]}): active={row[3]}")

if not rows:
    print("  None found")

conn.close()
