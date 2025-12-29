from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from enum import Enum
from aos.core.config import settings
from aos.core.security.identity import NodeIdentityManager


class AosRole(str, Enum):
    ROOT = "root"              # Full kernel access (Super Admin)
    ADMIN = "admin"            # Regional / Organization management
    COMMUNITY_ADMIN = "community_admin"  # Single community management
    OPERATOR = "operator"      # Data entry and field operations
    VIEWER = "viewer"          # Read-only access

    @property
    def level(self) -> int:
        """Numeric level for hierarchical comparison."""
        return {
            AosRole.ROOT: 5,
            AosRole.ADMIN: 4,
            AosRole.COMMUNITY_ADMIN: 3,
            AosRole.OPERATOR: 2,
            AosRole.VIEWER: 1
        }[self]


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
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(seconds=expires_in)
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

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
        payload = auth_manager.verify_token(token)
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

def requires_role(minimum_role: AosRole):
    """
    Dependency to enforce hierarchical RBAC.
    """
    async def role_checker(current_user: dict = Depends(get_current_operator)):
        user_role_str = current_user.get("role", "viewer")
        try:
            user_role = AosRole(user_role_str)
        except ValueError:
            user_role = AosRole.VIEWER

        if user_role.level < minimum_role.level:
            from aos.core.security.audit import AuditLogger
            audit = AuditLogger()
            audit.log_event("UNAUTHORIZED_ACCESS", {
                "user": current_user.get("username"),
                "required": minimum_role.value,
                "found": user_role.value
            }, severity="WARNING")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {minimum_role.value} privileges."
            )
        return current_user
    
    return role_checker

def requires_community_access(group_id_param: str = "group_id"):
    """
    Dependency to enforce community-level isolation.
    Root and Admin roles bypass this.
    Community Admin must match the community_id.
    """
    async def access_checker(
        request: Request,
        current_user: dict = Depends(get_current_operator)
    ):
        # 1. Root/Admin bypass
        user_role_str = current_user.get("role", "viewer")
        try:
            user_role = AosRole(user_role_str)
        except ValueError:
            user_role = AosRole.VIEWER

        if user_role.level >= AosRole.ADMIN.level:
            return current_user

        # 2. Extract group_id from path or query
        target_group_id = request.path_params.get(group_id_param)
        if not target_group_id:
            target_group_id = request.query_params.get(group_id_param)

        # 3. Check community_id match
        user_community_id = current_user.get("community_id")
        
        if user_role == AosRole.COMMUNITY_ADMIN:
            if not target_group_id:
                # If they didn't specify a group, we can't let them see "all"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You must specify a community ID."
                )
            
            if user_community_id == target_group_id:
                return current_user
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not manage this community."
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrative privileges."
        )

    return access_checker
