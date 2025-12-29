import sqlite3

def cleanup_duplicates():
    conn = sqlite3.connect("aos.db")
    cursor = conn.cursor()
    
    # Get all groups
    cursor.execute("SELECT id, name, location FROM community_groups")
    groups = cursor.fetchall()
    
    seen = {} # (name, location) -> primary_id
    duplicates_removed = 0
    members_reassigned = 0
    
    for g_id, name, loc in groups:
        key = (name, loc)
        if key not in seen:
            seen[key] = g_id
        else:
            # This is a duplicate!
            primary_id = seen[key]
            
            # Reassign members from this duplicate to the primary group
            cursor.execute("UPDATE community_members SET community_id = ? WHERE community_id = ?", (primary_id, g_id))
            members_reassigned += cursor.rowcount
            
            # Delete the duplicate group
            cursor.execute("DELETE FROM community_groups WHERE id = ?", (g_id,))
            duplicates_removed += 1
            
    # Also cleanup members with invalid IDs (like GRP-0 if they exist)
    # Check for members whose community_id doesn't exist anymore
    cursor.execute("SELECT DISTINCT community_id FROM community_members")
    current_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM community_groups")
    valid_group_ids = [row[0] for row in cursor.fetchall()]
    
    invalid_count = 0
    for cid in current_ids:
        if cid not in valid_group_ids:
            # Delete members with invalid group IDs
            cursor.execute("DELETE FROM community_members WHERE community_id = ?", (cid,))
            invalid_count += cursor.rowcount
            
    conn.commit()
    conn.close()
    
    print(f"Cleanup complete!")
    print(f"- Duplicates removed: {duplicates_removed}")
    print(f"- Members reassigned: {members_reassigned}")
    print(f"- Orphaned members removed: {invalid_count}")

if __name__ == "__main__":
    cleanup_duplicates()
