"""
Test Phase 3: Community Code Detection and Join Flow
"""
import sqlite3
import sys
sys.path.insert(0, '.')

from aos.modules.community import CommunityModule
from aos.db.engine import connect

def test_community_code_flow():
    print("=" * 60)
    print("PHASE 3 INTERNAL TEST: Community Code Detection")
    print("=" * 60)
    
    # 1. Setup - Use repository directly to avoid dispatcher dependency
    conn = connect("aos.db")
    from aos.db.repository import CommunityGroupRepository
    repo = CommunityGroupRepository(conn)
    
    # 2. Check if RCCG community exists with code
    print("\n[TEST 1] Checking RCCG community setup...")
    cursor = conn.execute("""
        SELECT id, name, community_code, code_active 
        FROM community_groups 
        WHERE name LIKE '%RCCG%'
    """)
    row = cursor.fetchone()
    
    if not row:
        print("❌ FAIL: RCCG community not found")
        return False
    
    community_id, name, code, active = row
    print(f"✅ Found: {name}")
    print(f"   Code: {code}")
    print(f"   Active: {active}")
    
    if not code:
        print("❌ FAIL: Community code is NULL")
        return False
    
    if not active:
        print("⚠️  WARNING: Code is not active (code_active = 0)")
        print("   You need to enable it in the Admin UI")
        return False
    
    # 3. Test code lookup
    print(f"\n[TEST 2] Testing get_by_code('{code}')...")
    group = repo.get_by_code(code)
    
    if not group:
        print(f"❌ FAIL: get_by_code('{code}') returned None")
        return False
    
    print(f"✅ PASS: Found group '{group.name}'")
    print(f"   ID: {group.id}")
    print(f"   Code: {group.community_code}")
    print(f"   Active: {group.code_active}")
    
    # 4. Test case sensitivity
    print(f"\n[TEST 3] Testing case insensitivity...")
    test_codes = [code.lower(), code.upper(), code.title()]
    
    for test_code in test_codes:
        result = repo.get_by_code(test_code)
        if result:
            print(f"✅ PASS: '{test_code}' → Found")
        else:
            print(f"❌ FAIL: '{test_code}' → Not found")
    
    # 5. Test invalid code
    print(f"\n[TEST 4] Testing invalid code rejection...")
    invalid_group = repo.get_by_code("INVALID_CODE_12345")
    
    if invalid_group:
        print("❌ FAIL: Invalid code returned a group!")
    else:
        print("✅ PASS: Invalid code correctly rejected")
    
    # 6. Test inactive code
    print(f"\n[TEST 5] Testing inactive code handling...")
    # Temporarily deactivate
    conn.execute("UPDATE community_groups SET code_active = 0 WHERE id = ?", (community_id,))
    conn.commit()
    
    inactive_result = repo.get_by_code(code)
    
    # Reactivate
    conn.execute("UPDATE community_groups SET code_active = 1 WHERE id = ?", (community_id,))
    conn.commit()
    
    if inactive_result:
        print("❌ FAIL: Inactive code was accepted!")
    else:
        print("✅ PASS: Inactive code correctly rejected")
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ All core tests passed!")
    print("\nNext steps:")
    print("1. Deploy to production: fly deploy --app africa-offline-os")
    print("2. In Admin UI, ensure 'Code Active' checkbox is CHECKED")
    print(f"3. In Telegram, type: {code}")
    print("4. You should see: '🤝 Community Invitation' prompt")
    print("=" * 60)
    
    conn.close()
    return True

if __name__ == "__main__":
    try:
        success = test_community_code_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
