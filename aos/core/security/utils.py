from __future__ import annotations

import uuid

from aos.core.security.auth import auth_manager


def generate_root_token(expires_in_days: int = 30) -> str:
    """
    Generate a long-lived root management token for the local operator.
    This should be used during initial setup or rescue.
    """
    payload = {
        "sub": f"root-{uuid.uuid4().hex[:8]}",
        "role": "admin",
        "scopes": ["*"]
    }
    return auth_manager.issue_token(payload, expires_in=expires_in_days * 86400)

if __name__ == "__main__":
    # Simple CLI helper: python -m aos.core.security.utils
    print("--- A-OS ROOT TOKEN GENERATOR ---")
    token = generate_root_token()
    print(f"Token: {token}")
    print("--------------------------------")
