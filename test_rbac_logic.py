import asyncio
from unittest.mock import MagicMock
from fastapi import Request, HTTPException
from aos.core.security.auth import AosRole, requires_community_access

async def test_rbac():
    # Setup
    access_checker = requires_community_access(group_id_param="group_id")
    
    # Mock current_user (Community Admin)
    comm_admin = {
        "role": "community_admin",
        "community_id": "GRP-123",
        "username": "comm_admin"
    }
    
    # 1. Test allowed access
    req_allowed = MagicMock(spec=Request)
    req_allowed.path_params = {"group_id": "GRP-123"}
    
    result = await access_checker(req_allowed, current_user=comm_admin)
    assert result == comm_admin
    print("✅ Community Admin allowed to access their own group.")
    
    # 2. Test denied access
    req_denied = MagicMock(spec=Request)
    req_denied.path_params = {"group_id": "GRP-456"}
    
    try:
        await access_checker(req_denied, current_user=comm_admin)
        print("❌ FAILED: Community Admin allowed to access OTHER group.")
    except HTTPException as e:
        assert e.status_code == 403
        assert "Access denied" in e.detail
        print("✅ Community Admin denied access to other group.")
        
    # 3. Test super admin bypass (ROOT)
    root_user = {
        "role": "root",
        "username": "root"
    }
    req_root = MagicMock(spec=Request)
    req_root.path_params = {"group_id": "GRP-456"}
    
    result = await access_checker(req_root, current_user=root_user)
    assert result == root_user
    print("✅ Role 'root' bypassed community check.")

    # 4. Test super admin bypass (ADMIN)
    admin_user = {
        "role": "admin",
        "username": "admin"
    }
    result = await access_checker(req_root, current_user=admin_user)
    assert result == admin_user
    print("✅ Role 'admin' bypassed community check.")

if __name__ == "__main__":
    asyncio.run(test_rbac())
