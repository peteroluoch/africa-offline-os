import pytest
from fastapi.testclient import TestClient
from aos.api.app import create_app, reset_globals

app = create_app()
client = TestClient(app)

def test_logout_clears_cookie():
    # Simulate a logged in state is not strictly necessary for testing the logout endpoint's behavior
    # but we can check if it sets the cookie to empty/expired.
    
    response = client.get("/auth/logout", follow_redirects=False)
    
    # Debug
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    
    # Check redirect
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    
    # Check cookie deletion
    cookies = response.headers.get_list("set-cookie")
    print(f"Set-Cookie: {cookies}")
    cookie = next((c for c in cookies if "access_token" in c), None)
    assert cookie is not None
    # On most systems it will be something like access_token=""; Max-Age=0; ...
    assert 'access_token=' in cookie
    assert "Max-Age=0" in cookie or 'expires=Thu, 01 Jan 1970 00:00:00 GMT' in cookie

def test_logout_post_clears_cookie():
    response = client.post("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    
    cookie = next((c for c in response.headers.get_list("set-cookie") if "access_token" in c), None)
    assert cookie is not None
