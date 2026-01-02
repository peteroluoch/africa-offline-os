import sqlite3

conn = sqlite3.connect("aos.db")
cursor = conn.execute("SELECT id, name, community_code, code_active FROM community_groups WHERE name LIKE '%RCCG%'")
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Code: {row[2]}")
    print(f"Active: {row[3]}")
    print("---")

conn.close()
