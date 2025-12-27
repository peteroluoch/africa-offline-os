import pytest
from fastapi.testclient import TestClient
from aos.api.app import create_app
from aos.core.security.auth import auth_manager, AosRole

app = create_app()
client = TestClient(app)

def test_rbac_user_list_forbidden_for_viewer():
    # 1. Issue a VIEWER token
    token = auth_manager.issue_token(payload={
        "sub": "test_viewer",
        "username": "viewer_user",
        "role": AosRole.VIEWER.value
    })
    
    with client as c:
        # 2. Attempt to access admin users list
        c.cookies.set("access_token", f"Bearer {token}")
        response = c.get("/dashboard/users", follow_redirects=False)
        
        # 3. Assert Forbidden (403)
        assert response.status_code == 403
        assert "requires admin privileges" in response.json()["detail"].lower()

def test_rbac_user_list_allowed_for_admin():
    # 1. Issue an ADMIN token
    token = auth_manager.issue_token(payload={
        "sub": "test_admin",
        "username": "admin_user",
        "role": AosRole.ADMIN.value
    })
    
    with client as c:
        # 2. Attempt to access admin users list
        c.cookies.set("access_token", f"Bearer {token}")
        response = c.get("/dashboard/users", follow_redirects=False)
        
        # 3. Assert OK (200)
        assert response.status_code == 200
