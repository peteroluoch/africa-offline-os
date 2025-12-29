from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aos.api.state import community_state
from aos.core.security.auth import get_current_operator
from aos.db.models import CommunityGroupDTO

router = APIRouter(prefix="/community", tags=["community"])
templates = Jinja2Templates(directory="aos/api/templates")

@router.get("/", response_class=HTMLResponse)
async def community_dashboard(request: Request, page: int = 1, operator=Depends(get_current_operator)):
    pagination_data = community_state.module.list_groups(page=page, per_page=10) if community_state.module else {
        "groups": [],
        "total": 0,
        "page": 1,
        "per_page": 10,
        "total_pages": 0
    }
    
    # Mock some counts for the dashboard
    broadcasts_count = 0
    if community_state.module:
        broadcasts_count = len(community_state.module._announcements.list_all())

    return templates.TemplateResponse("community.html", {
        "request": request,
        "user": operator,
        **pagination_data,  # Unpack pagination data
        "broadcasts_count": broadcasts_count,
        "inquiry_hits": 0
    })

@router.get("/register", response_class=HTMLResponse)
async def community_register_form(request: Request, operator=Depends(get_current_operator)):
    return templates.TemplateResponse("partials/community_group_form.html", {"request": request, "user": operator})

@router.post("/register")
async def register_community_group(
    request: Request,
    name: str = Form(...),
    group_type: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    operator=Depends(get_current_operator)
):
    if community_state.module:
        await community_state.module.register_group(
            name=name,
            tags=[group_type] if group_type else [],
            location=location or "Unknown",
            admin_id=operator.get("sub"),
            group_type=group_type,
            description=description
        )
    return RedirectResponse(url="/community", status_code=303)

@router.delete("/{group_id}")
async def delete_community_group(
    group_id: str,
    operator=Depends(get_current_operator)
):
    """Deactivate a community group (Soft Delete)."""
    if community_state.module:
        success = await community_state.module.deactivate_group(
            group_id=group_id,
            admin_id=operator.get("sub")
        )
        if success:
            return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Group not found")

@router.get("/{group_id}/members", response_class=HTMLResponse)
async def list_group_members(
    request: Request,
    group_id: str,
    operator=Depends(get_current_operator)
):
    """List all members of a community group."""
    members = []
    group = None
    
    if community_state.module:
        group = community_state.module.get_group(group_id)
        if group:
            members = community_state.module.get_community_members(group_id)
    
    return templates.TemplateResponse("partials/community_members.html", {
        "request": request,
        "user": operator,
        "group": group,
        "members": members
    })

@router.post("/{group_id}/members")
async def add_group_member(
    group_id: str,
    user_id: str = Form(...),
    channel: str = Form(...),
    operator=Depends(get_current_operator)
):
    """Add a member to a community group (Admin only)."""
    if community_state.module:
        await community_state.module.add_member_to_community(
            community_id=group_id,
            user_id=user_id,
            channel=channel
        )
    return RedirectResponse(url=f"/community/{group_id}/members", status_code=303)

@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    channel: str,
    operator=Depends(get_current_operator)
):
    """Remove a member from a community group (Admin only)."""
    if community_state.module:
        success = await community_state.module.remove_member_from_community(
            community_id=group_id,
            user_id=user_id,
            channel=channel
        )
        if success:
            return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Member not found")
