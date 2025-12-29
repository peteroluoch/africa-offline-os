"""
Quick test to verify database persistence after update.
"""
import sqlite3
from aos.db.engine import connect

# Connect to database
conn = connect("aos.db")
cursor = conn.cursor()

# Get a group before update
print("=== BEFORE UPDATE ===")
cursor.execute("SELECT id, name, group_type, description FROM community_groups WHERE name LIKE '%Mary%' LIMIT 1")
row = cursor.fetchone()
if row:
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Type: {row[2]}")
    print(f"Description: {row[3]}")
    group_id = row[0]
    
    # Simulate an update
    print("\n=== SIMULATING UPDATE ===")
    new_description = "Updated: Weekly mass and community outreach programs - TEST"
    cursor.execute("""
        UPDATE community_groups 
        SET description = ?, group_type = 'church'
        WHERE id = ?
    """, (new_description, group_id))
    conn.commit()
    print(f"Updated description to: {new_description}")
    
    # Verify the update persisted
    print("\n=== AFTER UPDATE (VERIFICATION) ===")
    cursor.execute("SELECT id, name, group_type, description FROM community_groups WHERE id = ?", (group_id,))
    updated_row = cursor.fetchone()
    if updated_row:
        print(f"ID: {updated_row[0]}")
        print(f"Name: {updated_row[1]}")
        print(f"Type: {updated_row[2]}")
        print(f"Description: {updated_row[3]}")
        
        if updated_row[3] == new_description:
            print("\n✅ DATABASE PERSISTENCE CONFIRMED!")
        else:
            print("\n❌ UPDATE DID NOT PERSIST!")
else:
    print("No group found matching criteria")

conn.close()
