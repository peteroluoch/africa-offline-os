#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("/data/aos.db")

# Check columns
cursor = conn.execute("PRAGMA table_info(community_groups)")
cols = {row[1] for row in cursor.fetchall()}

print("Has community_code:", "community_code" in cols)
print("Has code_active:", "code_active" in cols)

# Check RCCG community
if "community_code" in cols:
    cursor = conn.execute("""
        SELECT id, name, community_code, code_active 
        FROM community_groups 
        WHERE name LIKE '%RCCG%'
    """)
    row = cursor.fetchone()
    if row:
        print(f"\nRCCG Community:")
        print(f"  ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  Code: {row[2]}")
        print(f"  Active: {row[3]}")
    else:
        print("\nNo RCCG community found")

conn.close()
