"""
Admin User Management Router
Manages Telegram users, roles, and system operations.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from aos.core.users import UniversalUserService
from aos.core.security.auth import get_current_operator, requires_role, AosRole
from aos.api.app import get_db
import logging
import sqlite3
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["admin"])
templates = Jinja2Templates(directory="aos/api/templates")

@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request, 
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(requires_role(AosRole.ADMIN))
):
    """Display all Telegram users."""
    user_service = UniversalUserService()
    
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT * FROM telegram_users 
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    
    # Convert to dicts and parse roles
    import json
    users = []
    for row in rows:
        user = dict(row)
        user['roles'] = json.loads(user['roles'])
        users.append(user)
    
    # Calculate stats
    total_users = len(users)
    roles_count = {}
    for user in users:
        for role in user['roles']:
            roles_count[role] = roles_count.get(role, 0) + 1
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user": current_user,  # Dashboard template expects 'user'
        "users": users,
        "total_users": total_users,
        "roles_count": roles_count,
        "username": current_user["username"]
    })

@router.get("/users/{chat_id}", response_class=HTMLResponse)
async def user_detail(request: Request, chat_id: int, current_user: dict = Depends(get_current_operator)):
    """Display individual user details."""
    user_service = UniversalUserService()
    user = user_service.get_user_by_chat_id(chat_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return templates.TemplateResponse("admin_user_detail.html", {
        "request": request,
        "user": current_user,  # Dashboard template expects 'user' object
        "telegram_user": user,  # Rename to avoid confusion
        "username": current_user["username"],
        "available_roles": user_service.VALID_ROLES
    })

@router.post("/users/{chat_id}/roles")
async def update_user_roles(
    request: Request, 
    chat_id: int, 
    current_user: dict = Depends(get_current_operator),
    db: sqlite3.Connection = Depends(get_db)
):
    """Update user roles."""
    form_data = await request.form()
    selected_roles = form_data.getlist("roles")
    
    user_service = UniversalUserService()
    user = user_service.get_user_by_chat_id(chat_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update roles in database
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE telegram_users 
        SET roles = ?, updated_at = CURRENT_TIMESTAMP
        WHERE chat_id = ?
    """, (json.dumps(selected_roles), chat_id))
    
    db.commit()
    
    logger.info(f"Admin {current_user['username']} updated roles for user {chat_id}: {selected_roles}")
    
    return RedirectResponse(url=f"/dashboard/users/{chat_id}", status_code=303)

@router.post("/users/{chat_id}/domain")
async def set_user_domain(
    request: Request,
    chat_id: int,
    current_user: dict = Depends(get_current_operator)
):
    """Set user's active domain."""
    form_data = await request.form()
    domain = form_data.get("domain")
    
    user_service = UniversalUserService()
    success = user_service.set_active_domain(chat_id, domain)
    
    if success:
        logger.info(f"Admin {current_user['username']} set domain to {domain} for user {chat_id}")
        return RedirectResponse(url=f"/dashboard/users/{chat_id}", status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Failed to update domain")
