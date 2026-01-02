import sqlite3

conn = sqlite3.connect("aos.db")
cursor = conn.execute("SELECT name, community_code, code_active FROM community_groups WHERE name LIKE '%Umoja%'")
row = cursor.fetchone()

if row:
    print(f"Name: {row[0]}")
    print(f"Code: |{row[1]}|")
    print(f"Active: {row[2]}")
    if row[1]:
        print(f"Code length: {len(row[1])} chars")
        print(f"Code repr: {repr(row[1])}")
else:
    print("No Umoja community found")

conn.close()
