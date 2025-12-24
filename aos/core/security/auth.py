from __future__ import annotations
import jwt
import time
from datetime import datetime, timedelta, timezone
from aos.core.security.identity import NodeIdentityManager
from aos.core.config import settings

class AuthManager:
    """
    Stateless JWT Authentication Manager.
    Uses the Node's Ed25519 identity for signing and verifying tokens.
    """
    
    ALGORITHM = "EdDSA"
    
    def __init__(self, identity_manager: NodeIdentityManager | None = None):
        self.identity = identity_manager or NodeIdentityManager()
        # Note: We need the actual cryptography key objects for PyJWT
        # NodeIdentityManager currently returns bytes. We'll access the private key object.

    def issue_token(self, payload: dict, expires_in: int = 3600) -> str:
        """Issue a signed JWT token."""
        if not self.identity._private_key:
            self.identity.ensure_identity()
            
        data = payload.copy()
        data.update({
            "iss": settings.jwt_issuer,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        })
        
        return jwt.encode(data, self.identity._private_key, algorithm=self.ALGORITHM)

    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token."""
        if not self.identity._public_key:
            self.identity.ensure_identity()
            
        try:
            return jwt.decode(
                token, 
                self.identity._public_key, 
                algorithms=[self.ALGORITHM],
                issuer=settings.jwt_issuer
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidSignatureError:
            raise ValueError("Invalid signature")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)
auth_manager = AuthManager()

async def get_current_operator(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme)
) -> dict:
    """
    Validate JWT from Cookie OR Bearer token.
    Cookie takes precedence for browser flows.
    """
    token = None
    
    # 1. Check Cookie
    cookie_auth = request.cookies.get("access_token")
    if cookie_auth:
        # Expect format "Bearer <token>"
        parts = cookie_auth.split(" ")
        if len(parts) == 2:
            token = parts[1]
            
    # 2. Check Header (fallback)
    if not token and credentials:
        token = credentials.credentials
        
    if not token:
        # Redirect to login if browser request?
        # For API, return 401. 
        # Since we use this for dashboard (browser), we might want 401 and let client handle, 
        # OR 303 Redirect if it's a GET /dashboard request...
        # But dependencies shouldn't redirect easily.
        # We raise 401, logic elsewhere handles it.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return auth_manager.verify_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
