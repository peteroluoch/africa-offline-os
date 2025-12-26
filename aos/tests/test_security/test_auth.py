
import pytest

from aos.core.security.auth import AuthManager
from aos.core.security.identity import NodeIdentityManager


@pytest.fixture
def identity_manager(tmp_path):
    """Fixture for NodeIdentityManager."""
    manager = NodeIdentityManager(tmp_path / "keys")
    manager.ensure_identity()
    return manager

@pytest.fixture
def auth_manager(identity_manager):
    """Fixture for AuthManager."""
    return AuthManager(identity_manager)

def test_token_issuance_and_verification(auth_manager):
    """Verify that tokens can be issued and verified."""
    payload = {"sub": "operator-1", "role": "admin"}
    token = auth_manager.issue_token(payload, expires_in=3600)

    decoded = auth_manager.verify_token(token)
    assert decoded["sub"] == "operator-1"
    assert decoded["role"] == "admin"
    assert "exp" in decoded

def test_token_expiration(auth_manager):
    """Verify that expired tokens are rejected."""
    payload = {"sub": "short-lived"}
    token = auth_manager.issue_token(payload, expires_in=-10) # Already expired

    with pytest.raises(ValueError, match="Token has expired"):
        auth_manager.verify_token(token)

def test_invalid_signature(auth_manager, tmp_path):
    """Verify that tokens signed by a different identity are rejected."""
    payload = {"sub": "imposter"}
    token = auth_manager.issue_token(payload)

    # Create a different manager/key
    other_id = NodeIdentityManager(tmp_path / "other_keys")
    other_id.ensure_identity()
    other_auth = AuthManager(other_id)

    with pytest.raises(ValueError, match="Invalid signature"):
        other_auth.verify_token(token)

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from aos.core.security.auth import get_current_operator


@pytest.mark.asyncio
async def test_get_current_operator_dependency(auth_manager, monkeypatch):
    """Verify the FastAPI dependency works with valid credentials."""
    token = auth_manager.issue_token({"sub": "admin"}, expires_in=3600)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Patch the global auth_manager used in the dependency
    from aos.core.security import auth
    monkeypatch.setattr(auth, "auth_manager", auth_manager)

    payload = await get_current_operator(credentials)
    assert payload["sub"] == "admin"

@pytest.mark.asyncio
async def test_get_current_operator_invalid(auth_manager, monkeypatch):
    """Verify the FastAPI dependency raises 401 for invalid tokens."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

    from aos.core.security import auth
    monkeypatch.setattr(auth, "auth_manager", auth_manager)

    with pytest.raises(HTTPException) as exc:
        await get_current_operator(credentials)
    assert exc.value.status_code == 401

def test_tampered_token(auth_manager):
    """Verify that tampered tokens are rejected."""
    token = auth_manager.issue_token({"sub": "victim"})

    # Tamper with the token (JWT is header.payload.signature)
    parts = token.split(".")
    import base64
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    payload["sub"] = "attacker"
    new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    tampered_token = f"{parts[0]}.{new_payload}.{parts[2]}"

    with pytest.raises(ValueError, match="Invalid signature"):
        auth_manager.verify_token(tampered_token)

import json
