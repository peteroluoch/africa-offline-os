"""
RBAC Route Guard Middleware
Enforces access control at the application level before any route handler executes.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from aos.core.security.auth import AosRole
import re

# Route access control rules based on RBAC_ACCESS_MATRIX.md
ROUTE_ACCESS_RULES = {
    # System-level routes (SUPER_ADMIN only)
    r"^/sys/mesh": [AosRole.ROOT],
    
    # Admin routes (SUPER_ADMIN + SYSTEM_ADMIN)
    r"^/security": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    r"^/operators": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    r"^/dashboard/users": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    r"^/regional": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    r"^/sys/gallery": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    
    # Module routes (SUPER_ADMIN + SYSTEM_ADMIN)
    r"^/agri": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    r"^/transport": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    
    # Community registration (SUPER_ADMIN + SYSTEM_ADMIN)
    r"^/community/register": [AosRole.ROOT, AosRole.SYSTEM_ADMIN],
    
    # Main dashboard - special handling
    r"^/dashboard$": "ALL_AUTHENTICATED",
    
    # Community routes - handled by requires_community_access dependency
    r"^/community/": "COMMUNITY_SCOPED",
}

# Routes that should redirect isolated roles
REDIRECT_ROUTES = {
    r"^/dashboard$": True,
    r"^/community/?$": True,  # Main community list
}

async def rbac_route_guard(request: Request, call_next):
    """
    Middleware to enforce RBAC at route level.
    Runs before any route handler.
    """
    path = request.url.path
    
    # Skip auth routes and static files
    if path.startswith(("/auth/", "/static/", "/login", "/signup")):
        return await call_next(request)
    
    # Get user from request state (set by get_current_operator dependency)
    # For middleware, we need to check cookies directly
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        # Not authenticated - let the route handler's dependency handle it
        return await call_next(request)
    
    # Extract role from token
    try:
        from aos.core.security.auth import auth_manager
        token = access_token.replace("Bearer ", "")
        payload = auth_manager.verify_token(token)
        user_role_str = payload.get("role", "viewer")
        community_id = payload.get("community_id")
        
        try:
            user_role = AosRole(user_role_str)
        except ValueError:
            user_role = AosRole.VIEWER
            
    except Exception:
        # Invalid token - let route handler deal with it
        return await call_next(request)
    
    # Check if this is a redirect route for isolated roles
    if user_role in [AosRole.COMMUNITY_ADMIN, AosRole.OPERATOR]:
        for pattern in REDIRECT_ROUTES:
            if re.match(pattern, path):
                if community_id:
                    return RedirectResponse(
                        url=f"/community/{community_id}",
                        status_code=status.HTTP_303_SEE_OTHER
                    )
                else:
                    return RedirectResponse(
                        url="/unassigned",
                        status_code=status.HTTP_303_SEE_OTHER
                    )
    
    # Check route access rules
    for pattern, allowed_roles in ROUTE_ACCESS_RULES.items():
        if re.match(pattern, path):
            # Special handling for community-scoped routes
            if allowed_roles == "COMMUNITY_SCOPED":
                # Let the requires_community_access dependency handle it
                break
            
            # Special handling for all authenticated users
            if allowed_roles == "ALL_AUTHENTICATED":
                # Already handled by redirect logic above
                break
            
            # Check if user's role is in allowed list
            if user_role not in allowed_roles:
                # Log unauthorized access attempt
                from aos.core.security.audit import AuditLogger
                audit = AuditLogger()
                audit.log_event("RBAC_ROUTE_DENIED", {
                    "user": payload.get("username"),
                    "role": user_role.value,
                    "path": path,
                    "required_roles": [r.value for r in allowed_roles]
                }, severity="WARNING")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. This resource requires {' or '.join([r.value for r in allowed_roles])} privileges."
                )
    
    # Route is allowed, continue
    return await call_next(request)
