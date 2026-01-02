#!/usr/bin/env python3
import sqlite3
import sys

# Connect to production database
conn = sqlite3.connect("/data/aos.db")
cursor = conn.execute("""
    SELECT id, name, community_code, code_active 
    FROM community_groups 
    WHERE community_code IS NOT NULL
""")

print("Communities with codes in production:")
print("=" * 60)
for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Code: '{row[2]}'")
    print(f"Active: {row[3]}")
    print("-" * 60)

conn.close()
