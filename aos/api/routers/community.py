from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from aos.api.state import community_state
from aos.core.security.auth import get_current_operator, AosRole, requires_community_access

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
    # RBAC: Redirect community admin to their specific group
    if operator.get("role") == AosRole.COMMUNITY_ADMIN.value:
        comm_id = operator.get("community_id")
        if comm_id:
            return RedirectResponse(url=f"/community/{comm_id}", status_code=status.HTTP_303_SEE_OTHER)
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
    if AosRole(operator.get("role", "viewer")).level < AosRole.ADMIN.level:
        raise HTTPException(403, "Access denied: Only system admins can register new communities.")
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
    if AosRole(operator.get("role", "viewer")).level < AosRole.ADMIN.level:
        raise HTTPException(403, "Access denied: Only system admins can register new communities.")
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
    operator=Depends(requires_community_access())
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
    operator=Depends(requires_community_access())
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
    operator=Depends(requires_community_access())
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
    # RBAC: Enforce community isolation
    if operator.get("role") == AosRole.COMMUNITY_ADMIN.value:
        user_comm_id = operator.get("community_id")
        if not group_id:
            # Redirect to their own group if not specified
            return RedirectResponse(
                url=f"/community/members?group_id={user_comm_id}", 
                status_code=status.HTTP_303_SEE_OTHER
            )
        if group_id != user_comm_id:
            raise HTTPException(403, "Access denied: You do not manage this community.")
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
    # RBAC: Enforce community isolation
    if operator.get("role") == AosRole.COMMUNITY_ADMIN.value:
        user_comm_id = operator.get("community_id")
        if not group_id or group_id != user_comm_id:
            raise HTTPException(403, "Access denied: You must export from your own community.")
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

    # RBAC: Enforce community isolation
    if operator.get("role") == AosRole.COMMUNITY_ADMIN.value:
        if member["community_id"] != operator.get("community_id"):
            raise HTTPException(403, "Access denied: You do not manage this community.")

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
        # RBAC: Fetch member to check community ownership
        res = community_state.module._db.execute(
            "SELECT community_id FROM community_members WHERE id = ?",
            (member_id,)
        ).fetchone()
        
        if not res:
            raise HTTPException(404, "Member not found")
            
        member_community_id = res[0]
        
        if operator.get("role") == AosRole.COMMUNITY_ADMIN.value:
            if member_community_id != operator.get("community_id"):
                raise HTTPException(403, "Access denied: You do not manage this community.")

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
    operator=Depends(requires_community_access())
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
    operator=Depends(requires_community_access())
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
    operator=Depends(requires_community_access())
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


# ========== BROADCAST UI ENDPOINTS ==========

@router.get("/{group_id}", response_class=HTMLResponse)
async def community_detail(
    group_id: str,
    request: Request,
    operator=Depends(requires_community_access())
):
    """Community detail page with broadcast UI."""
    if not community_state.module:
        raise HTTPException(500, "Community module not initialized")
    
    # Get group
    group = community_state.module.get_group(group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    
    # Get member count
    members = community_state.module.get_community_members(group_id)
    member_count = len(members)
    
    # Get broadcast stats for this group
    broadcast_stats = {"pending": 0, "sent": 0, "failed": 0}
    status_res = community_state.module._db.execute("""
        SELECT d.status, COUNT(*) 
        FROM broadcast_deliveries d
        JOIN broadcasts b ON d.broadcast_id = b.id
        WHERE b.community_id = ?
        GROUP BY d.status
    """, (group_id,)).fetchall()
    
    for status, count in status_res:
        if status in broadcast_stats:
            broadcast_stats[status] = count
    
    # Get recent broadcasts
    recent_broadcasts_raw = community_state.module._db.execute("""
        SELECT id, message, status, sent_count, failed_count, created_at
        FROM broadcasts
        WHERE community_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (group_id,)).fetchall()
    
    recent_broadcasts = [
        {
            "id": row[0],
            "message": row[1],
            "status": row[2],
            "sent_count": row[3],
            "failed_count": row[4],
            "created_at": datetime.fromisoformat(row[5].replace(' ', 'T')) if row[5] else None
        }
        for row in recent_broadcasts_raw
    ]
    
    return templates.TemplateResponse("community_detail.html", {
        "request": request,
        "user": operator,
        "group": group,
        "member_count": member_count,
        "broadcast_stats": broadcast_stats,
        "recent_broadcasts": recent_broadcasts
    })


@router.post("/{group_id}/broadcast", response_class=HTMLResponse)
async def send_broadcast(
    group_id: str,
    request: Request,
    message: str = Form(...),
    channel: str = Form("telegram"),
    cost_confirmed: bool = Form(False),
    operator=Depends(requires_community_access())
):
    """Send broadcast with cost guardrail."""
    if not community_state.module:
        raise HTTPException(500, "Community module not initialized")
    
    try:
        # Attempt to publish (will raise ValueError if cost confirmation needed)
        announcement = await community_state.module.publish_announcement(
            group_id=group_id,
            message=message,
            actor_id=operator.get("sub"),
            cost_confirmed=cost_confirmed
        )
        
        # Success - return success toast
        return templates.TemplateResponse("partials/broadcast_success.html", {
            "request": request,
            "group_id": group_id,
            "announcement_id": announcement.id
        })
        
    except ValueError as e:
        error_msg = str(e)
        if "COST_CONFIRMATION_REQUIRED" in error_msg:
            # Parse cost details from error message
            parts = error_msg.split("|")
            cost = parts[1].split(":")[1].strip().replace("KES ", "")
            recipients = parts[2].split(":")[1].strip()
            channels = parts[3].split(":")[1].strip()
            msg_length = parts[4].split(":")[1].strip().split()[0]
            
            # Return confirmation modal
            return templates.TemplateResponse("partials/broadcast_confirmation.html", {
                "request": request,
                "group_id": group_id,
                "message": message,
                "channel": channel,
                "cost": cost,
                "recipient_count": recipients,
                "channels": channels,
                "message_length": msg_length
            })
        else:
            raise HTTPException(400, str(e))


@router.post("/{group_id}/broadcast/confirm", response_class=HTMLResponse)
async def confirm_broadcast(
    group_id: str,
    request: Request,
    message: str = Form(...),
    channel: str = Form("telegram"),
    operator=Depends(requires_community_access())
):
    """Confirm and send expensive broadcast."""
    if not community_state.module:
        raise HTTPException(500, "Community module not initialized")
    
    # Send with cost_confirmed=True
    announcement = await community_state.module.publish_announcement(
        group_id=group_id,
        message=message,
        actor_id=operator.get("sub"),
        cost_confirmed=True
    )
    
    # Return success toast
    return templates.TemplateResponse("partials/broadcast_success.html", {
        "request": request,
        "group_id": group_id,
        "announcement_id": announcement.id
    })


@router.get("/{group_id}/broadcasts", response_class=HTMLResponse)
async def get_broadcast_history(
    group_id: str,
    request: Request,
    operator=Depends(requires_community_access())
):
    """Fetch broadcast history for HTMX refresh."""
    if not community_state.module:
        raise HTTPException(500, "Community module not initialized")
    
    # Get recent broadcasts
    recent_broadcasts_raw = community_state.module._db.execute("""
        SELECT id, message, status, sent_count, failed_count, created_at
        FROM broadcasts
        WHERE community_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (group_id,)).fetchall()
    
    recent_broadcasts = [
        {
            "id": row[0],
            "message": row[1],
            "status": row[2],
            "sent_count": row[3],
            "failed_count": row[4],
            "created_at": datetime.fromisoformat(row[5].replace(' ', 'T')) if row[5] else None
        }
        for row in recent_broadcasts_raw
    ]
    
    return templates.TemplateResponse("partials/broadcast_history_table.html", {
        "request": request,
        "recent_broadcasts": recent_broadcasts
    })
