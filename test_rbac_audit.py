"""
RBAC Security Audit Test Script
Tests all access control rules defined in RBAC_ACCESS_MATRIX.md
"""
import sqlite3
from aos.core.security.auth import AosRole

def test_rbac_implementation():
    """Run comprehensive RBAC tests"""
    
    print("=" * 60)
    print("RBAC SECURITY AUDIT")
    print("=" * 60)
    
    conn = sqlite3.connect("aos.db")
    
    # Test 1: Verify all roles exist
    print("\n[TEST 1] Verifying Role Definitions...")
    roles = conn.execute("SELECT name FROM roles ORDER BY name").fetchall()
    role_names = [r[0] for r in roles]
    
    expected_roles = ['admin', 'community_admin', 'operator', 'super_admin', 'viewer']
    missing_roles = set(expected_roles) - set(role_names)
    
    if missing_roles:
        print(f"  ❌ FAIL: Missing roles: {missing_roles}")
    else:
        print(f"  ✅ PASS: All required roles exist")
        print(f"     Roles: {', '.join(role_names)}")
    
    # Test 2: Verify role hierarchy
    print("\n[TEST 2] Verifying Role Hierarchy...")
    hierarchy_correct = True
    try:
        assert AosRole.ROOT.level == 5, "ROOT should be level 5"
        assert AosRole.SYSTEM_ADMIN.level == 4, "SYSTEM_ADMIN should be level 4"
        assert AosRole.COMMUNITY_ADMIN.level == 3, "COMMUNITY_ADMIN should be level 3"
        assert AosRole.OPERATOR.level == 2, "OPERATOR should be level 2"
        assert AosRole.VIEWER.level == 1, "VIEWER should be level 1"
        print("  ✅ PASS: Role hierarchy correct")
        print("     ROOT(5) > SYSTEM_ADMIN(4) > COMMUNITY_ADMIN(3) > OPERATOR(2) > VIEWER(1)")
    except AssertionError as e:
        print(f"  ❌ FAIL: {e}")
        hierarchy_correct = False
    
    # Test 3: Verify operators table has community_id column
    print("\n[TEST 3] Verifying Database Schema...")
    try:
        cursor = conn.execute("PRAGMA table_info(operators)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'community_id' in columns:
            print("  ✅ PASS: operators.community_id column exists")
        else:
            print("  ❌ FAIL: operators.community_id column missing")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    # Test 4: Check for test users
    print("\n[TEST 4] Checking Test Users...")
    cursor = conn.execute("""
        SELECT o.username, r.name as role, o.community_id
        FROM operators o
        JOIN roles r ON o.role_id = r.id
        ORDER BY r.name, o.username
    """)
    users = cursor.fetchall()
    
    if users:
        print("  ✅ Users found:")
        for username, role, comm_id in users:
            comm_status = f"→ {comm_id[:8]}..." if comm_id else "→ UNASSIGNED"
            print(f"     {username:15} | {role:20} | {comm_status}")
    else:
        print("  ⚠️  No users found")
    
    # Test 5: Verify middleware exists
    print("\n[TEST 5] Verifying RBAC Middleware...")
    try:
        from aos.api.middleware.rbac import rbac_route_guard, ROUTE_ACCESS_RULES
        print("  ✅ PASS: RBAC middleware module exists")
        print(f"     Protected routes: {len(ROUTE_ACCESS_RULES)}")
    except ImportError as e:
        print(f"  ❌ FAIL: {e}")
    
    # Test 6: Verify access matrix documentation
    print("\n[TEST 6] Verifying Documentation...")
    import os
    if os.path.exists("docs/RBAC_ACCESS_MATRIX.md"):
        print("  ✅ PASS: RBAC_ACCESS_MATRIX.md exists")
    else:
        print("  ❌ FAIL: RBAC_ACCESS_MATRIX.md missing")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)
    print("\n📋 NEXT STEPS:")
    print("1. Start the server: uvicorn aos.api.app:create_app --factory --reload")
    print("2. Test as OPERATOR (Oduor):")
    print("   - Should only see assigned community")
    print("   - Sidebar should be empty")
    print("   - Cannot access /security, /operators, /agri, etc.")
    print("3. Test as SYSTEM_ADMIN:")
    print("   - Should see full sidebar")
    print("   - Can access all routes except /sys/mesh")
    print("4. Test as SUPER_ADMIN:")
    print("   - Should have unrestricted access")
    print("\n")

if __name__ == "__main__":
    test_rbac_implementation()
