import sqlite3
import json

def check_members():
    conn = sqlite3.connect("aos.db")
    cursor = conn.cursor()
    
    print("\n--- GROUPS ---")
    cursor.execute("SELECT id, name FROM community_groups")
    groups = cursor.fetchall()
    for g in groups:
        print(f"ID: '{g[0]}' (len={len(g[0])}) | Name: '{g[1]}'")
        
    print("\n--- MEMBERS SAMPLE (First 5) ---")
    cursor.execute("SELECT user_id, community_id FROM community_members LIMIT 5")
    members = cursor.fetchall()
    for m in members:
        print(f"User: '{m[0]}' | Community ID: '{m[1]}' (len={len(m[1])})")
        
    # Check if Umoja SACCO has members
    cursor.execute("SELECT id, name FROM community_groups WHERE name LIKE '%Umoja%'")
    groups = cursor.fetchall()
    for g in groups:
        g_id, g_name = g
        print(f"\nGroup: '{g_name}' | ID: '{g_id}'")
        cursor.execute("SELECT COUNT(*) FROM community_members WHERE community_id = ?", (g_id,))
        count = cursor.fetchone()[0]
        print(f"Direct count by ID '{g_id}': {count}")
        
        # Test count by user_id like search
        cursor.execute("SELECT COUNT(*) FROM community_members m JOIN community_groups g ON m.community_id = g.id WHERE g.name = ?", (g_name,))
        count_by_name = cursor.fetchone()[0]
        print(f"Count by JOIN on Name '{g_name}': {count_by_name}")

    conn.close()

if __name__ == "__main__":
    check_members()
