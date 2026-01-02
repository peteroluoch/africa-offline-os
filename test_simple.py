import sqlite3

conn = sqlite3.connect("aos.db")

print("PHASE 3 TEST: Community Code Detection")
print("=" * 50)

# Test 1: Check database schema
print("\n[TEST 1] Database Schema Check")
cursor = conn.execute("PRAGMA table_info(community_groups)")
columns = [row[1] for row in cursor.fetchall()]

if "community_code" in columns:
    print("PASS: community_code column exists")
else:
    print("FAIL: community_code column missing")

if "code_active" in columns:
    print("PASS: code_active column exists")
else:
    print("FAIL: code_active column missing")

# Test 2: Check RCCG community
print("\n[TEST 2] RCCG Community Check")
cursor = conn.execute("""
    SELECT id, name, community_code, code_active 
    FROM community_groups 
    WHERE name LIKE '%RCCG%'
""")
row = cursor.fetchone()

if row:
    print(f"PASS: Found community")
    print(f"  Name: {row[1]}")
    print(f"  Code: {row[2]}")
    print(f"  Active: {row[3]}")
    
    if row[2]:
        print("PASS: Code is set")
    else:
        print("FAIL: Code is NULL")
    
    if row[3] == 1:
        print("PASS: Code is active")
    else:
        print("WARNING: Code is inactive")
else:
    print("FAIL: RCCG community not found")

# Test 3: Test repository lookup
print("\n[TEST 3] Repository Lookup Test")
from aos.db.repository import CommunityGroupRepository
repo = CommunityGroupRepository(conn)

if row and row[2]:
    test_code = row[2]
    result = repo.get_by_code(test_code)
    
    if result:
        print(f"PASS: get_by_code('{test_code}') found community")
    else:
        print(f"FAIL: get_by_code('{test_code}') returned None")

# Test 4: Invalid code
print("\n[TEST 4] Invalid Code Test")
invalid = repo.get_by_code("INVALID_CODE_999")
if invalid:
    print("FAIL: Invalid code returned a result")
else:
    print("PASS: Invalid code correctly rejected")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)

conn.close()
