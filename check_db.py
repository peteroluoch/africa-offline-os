import sqlite3
conn = sqlite3.connect("aos.db")
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT * FROM community_members")
rows = cursor.fetchall()
print(f"Total community members: {len(rows)}")
for row in rows:
    print(dict(row))
conn.close()
