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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer()
auth_manager = AuthManager()

async def get_current_operator(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """FastAPI dependency to validate JWT and return the operator payload."""
    try:
        return auth_manager.verify_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
