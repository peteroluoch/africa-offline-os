import sqlite3

conn = sqlite3.connect("aos.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check if invite_slug column exists and has data
cursor.execute("SELECT id, name, invite_slug FROM community_groups LIMIT 5")
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row['id']}, Name: {row['name']}, Slug: {row['invite_slug']}")

conn.close()
