from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from aos.core.security.auth import get_current_operator, requires_role, AosRole
from aos.api.dependencies import get_db
import sqlite3
import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operators", tags=["operators"])
templates = Jinja2Templates(directory="aos/api/templates")

@router.get("/", response_class=HTMLResponse)
async def list_operators(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(requires_role(AosRole.SYSTEM_ADMIN))
):
    """List all system operators for management."""
    cursor = db.execute("""
        SELECT o.id, o.username, r.name as role, o.community_id, g.name as community_name, o.created_at, o.last_login
        FROM operators o
        JOIN roles r ON o.role_id = r.id
        LEFT JOIN community_groups g ON o.community_id = g.id
        ORDER BY o.created_at DESC
    """)
    operators = [dict(row) for row in cursor.fetchall()]

    # Get available roles and communities for the modals
    roles = db.execute("SELECT name FROM roles").fetchall()
    communities = db.execute("SELECT id, name FROM community_groups WHERE active=1").fetchall()

    return templates.TemplateResponse("operators.html", {
        "request": request,
        "user": current_user,
        "operators": operators,
        "available_roles": [r[0] for r in roles],
        "available_communities": [{"id": c[0], "name": c[1]} for c in communities]
    })

@router.post("/{op_id}/update-role")
async def update_operator_role(
    op_id: str,
    role_name: str = Form(...),
    community_id: str = Form(None),
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(requires_role(AosRole.SYSTEM_ADMIN))
):
    """Update an operator's role and community assignment."""
    # 1. Prevent self-demotion or demoting ROOT if not ROOT
    if op_id == current_user.get("sub"):
        raise HTTPException(400, "You cannot modify your own role.")

    # 2. Get role ID
    role_row = db.execute("SELECT id FROM roles WHERE name=?", (role_name,)).fetchone()
    if not role_row:
        raise HTTPException(400, "Invalid role name.")
    role_id = role_row[0]

    # 3. Update operator
    db.execute(
        "UPDATE operators SET role_id = ?, community_id = ? WHERE id = ?",
        (role_id, community_id, op_id)
    )
    db.commit()

    logger.info(f"AUDIT: Admin {current_user['username']} updated operator {op_id} to {role_name} (Community: {community_id})")

    return RedirectResponse(url="/operators", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{op_id}/delete")
async def delete_operator(
    op_id: str,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(requires_role(AosRole.ROOT))
):
    """Delete an operator (ROOT only)."""
    if op_id == current_user.get("sub"):
        raise HTTPException(400, "You cannot delete yourself.")

    db.execute("DELETE FROM operators WHERE id = ?", (op_id,))
    db.commit()

    logger.info(f"AUDIT: Root {current_user['username']} deleted operator {op_id}")

    return RedirectResponse(url="/operators", status_code=status.HTTP_303_SEE_OTHER)
