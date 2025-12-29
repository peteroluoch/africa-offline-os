from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from aos.api.state import community_state
from aos.core.security.auth import get_current_operator

router = APIRouter(prefix="/community", tags=["community"])
templates = Jinja2Templates(directory="aos/api/templates")

@router.get("/", response_class=HTMLResponse)
async def community_dashboard(
    request: Request,
    page: int = 1,
    search: str = None,
    type: str = None,
    trust: str = None,
    operator=Depends(get_current_operator)
):
    pagination_data = community_state.module.list_groups(
        page=page,
        per_page=10,
        search_query=search,
        group_type=type,
        trust_level=trust
    ) if community_state.module else {
        "groups": [],
        "total": 0,
        "page": 1,
        "per_page": 10,
        "total_pages": 0
    }

    # Get all unique group types for filter dropdown
    group_types = []
    if community_state.module:
        group_types = community_state.module.get_group_types()

    # Broadcast Status Metrics (FAANG Dashboard Requirement)
    broadcast_stats = {"pending": 0, "sent": 0, "failed": 0, "total": 0}
    if community_state.module:
        # Count actual broadcasts from the queue table
        res = community_state.module._db.execute("SELECT COUNT(*) FROM broadcasts").fetchone()
        broadcasts_count = res[0] if res else 0
        broadcast_stats["total"] = broadcasts_count
        
        # Get delivery status breakdown
        status_res = community_state.module._db.execute("""
            SELECT status, COUNT(*) 
            FROM broadcast_deliveries 
            GROUP BY status
        """).fetchall()
        
        for status, count in status_res:
            if status in broadcast_stats:
                broadcast_stats[status] = count

    context = {
        "request": request,
        "user": operator,
        "search": search,
        "selected_type": type,
        "selected_trust": trust,
        "group_types": group_types,
        **pagination_data,
        "broadcasts_count": broadcasts_count,
        "broadcast_stats": broadcast_stats,
        "inquiry_hits": 0
    }

    # If HTMX request, return only the table partial
    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse("partials/community_groups_table.html", context)

    return templates.TemplateResponse("community.html", context)

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

@router.get("/{group_id}/edit", response_class=HTMLResponse)
async def edit_group_form(
    request: Request,
    group_id: str,
    operator=Depends(get_current_operator)
):
    """Show edit form for a group."""
    group = None
    if community_state.module:
        group = community_state.module.get_group(group_id)

    return templates.TemplateResponse("partials/community_group_edit.html", {
        "request": request,
        "user": operator,
        "group": group
    })

@router.put("/{group_id}")
async def update_community_group(
    group_id: str,
    name: str = Form(...),
    group_type: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    operator=Depends(get_current_operator)
):
    """Update a community group."""
    if community_state.module:
        group = community_state.module.get_group(group_id)
        if group:
            import json
            # Update group fields
            group.name = name
            group.group_type = group_type
            group.description = description
            group.location = location
            # Tags must be JSON string for SQLite
            group.tags = json.dumps([group_type] if group_type else [])

            # Save updated group
            community_state.module._groups.save(group)

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

@router.get("/members", response_class=HTMLResponse)
async def members_dashboard(
    request: Request,
    page: int = 1,
    group_id: str = None,
    channel: str = None,
    search: str = None,
    operator=Depends(get_current_operator)
):
    """Dedicated member management dashboard."""
    data = community_state.module.list_all_members(
        page=page,
        per_page=50,
        group_id=group_id,
        channel=channel,
        search_query=search
    ) if community_state.module else {
        "members": [],
        "total": 0,
        "page": 1,
        "per_page": 50,
        "total_pages": 0
    }

    # Get all groups for filter dropdown
    all_groups = []
    if community_state.module:
        all_groups = [g for g in community_state.module._groups.list_all() if g.active]

    # If HTMX request, return only the table partial
    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse("partials/community_members_table.html", {
            "request": request,
            "members": data["members"],
            "total": data["total"],
            "page": data["page"],
            "total_pages": data["total_pages"]
        })

    return templates.TemplateResponse("community_members.html", {
        "request": request,
        "user": operator,
        "members": data["members"],
        "total": data["total"],
        "page": data["page"],
        "total_pages": data["total_pages"],
        "all_groups": all_groups,
        "current_group": group_id,
        "current_channel": channel,
        "current_search": search
    })

@router.get("/members/export")
async def export_members(
    group_id: str = None,
    channel: str = None,
    search: str = None,
    operator=Depends(get_current_operator)
):
    """Export members as CSV."""
    data = community_state.module.list_all_members(
        page=1,
        per_page=1000000, # All members
        group_id=group_id,
        channel=channel,
        search_query=search
    ) if community_state.module else {"members": []}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Group", "Channel", "Joined At", "Status"])

    for m in data["members"]:
        writer.writerow([
            m["user_id"],
            m["group_name"],
            m["channel"],
            m["joined_at"].strftime('%Y-%m-%d %H:%M:%S') if m["joined_at"] else "N/A",
            "Active" if m["active"] else "Inactive"
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=community_members_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/members/{member_id}/edit", response_class=HTMLResponse)
async def edit_member_form(
    request: Request,
    member_id: str,
    operator=Depends(get_current_operator)
):
    """Fetch member edit modal content."""
    member = None
    if community_state.module:
        res = community_state.module._db.execute(
            "SELECT m.id, m.community_id, m.user_id, m.channel, g.name as group_name FROM community_members m JOIN community_groups g ON m.community_id = g.id WHERE m.id = ?",
            (member_id,)
        ).fetchone()
        if res:
            member = {
                "id": res[0],
                "community_id": res[1],
                "user_id": res[2],
                "channel": res[3],
                "group_name": res[4]
            }

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    return templates.TemplateResponse("partials/community_member_edit.html", {
        "request": request,
        "member": member
    })

@router.put("/members/{member_id}")
async def update_member_details(
    request: Request,
    member_id: str,
    user_id: str = Form(...),
    channel: str = Form(...),
    operator=Depends(get_current_operator)
):
    """Update member details (Admin only)."""
    if community_state.module:
        community_state.module.update_community_member(
            member_id=member_id,
            user_id=user_id,
            channel=channel,
            actor_id=operator.get("sub")
        )

    # Return the refreshed table partial for the Member Directory
    # We use default pagination (page 1) for the refresh
    return await members_dashboard(request, operator=operator)

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
            # Use list_all_members to get dictionaries with user_id, channel, etc.
            result = community_state.module.list_all_members(group_id=group_id, per_page=1000)
            members = result.get("members", [])

    return templates.TemplateResponse("partials/community_members.html", {
        "request": request,
        "user": operator,
        "group": group,
        "members": members
    })

@router.post("/{group_id}/members")
async def add_group_member(
    request: Request,
    group_id: str,
    user_id: str = Form(...),
    channel: str = Form(...),
    operator=Depends(get_current_operator)
):
    """Add a member to a community group (Admin only)."""
    if community_state.module:
        community_state.module.add_member_to_community(
            community_id=group_id,
            user_id=user_id,
            channel=channel,
            actor_id=operator.get("sub")
        )
    # Return the refreshed member list partial directly
    return await list_group_members(request, group_id, operator)

@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    channel: str,
    operator=Depends(get_current_operator)
):
    """Remove a member from a community group (Admin only)."""
    if community_state.module:
        community_state.module.remove_member_from_community(
            community_id=group_id,
            user_id=user_id,
            channel=channel,
            actor_id=operator.get("sub")
        )
        return HTMLResponse(status_code=204)

    raise HTTPException(status_code=404, detail="Member not found")
