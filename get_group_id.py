import sqlite3
import os

db_path = "aos.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM community_groups LIMIT 1")
    group = cursor.fetchone()
    if group:
        print(f"Group ID: {group[0]}, Name: {group[1]}")
    else:
        print("No groups found.")
    conn.close()
