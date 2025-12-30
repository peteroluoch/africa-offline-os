import sqlite3
import json

def list_communities():
    try:
        conn = sqlite3.connect("aos.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, location FROM community_groups WHERE active = 1")
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row['id']} | Name: {row['name']} | Location: {row['location']}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_communities()
