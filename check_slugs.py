import sqlite3

def check_slugs():
    conn = sqlite3.connect("aos.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, invite_slug FROM community_groups")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row['id']} | Name: {row['name']} | Slug: {row['invite_slug']}")
    conn.close()

if __name__ == "__main__":
    check_slugs()
