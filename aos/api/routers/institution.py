from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
import os
from typing import List, Optional
from datetime import datetime

from aos.db.models import InstitutionMemberDTO, InstitutionGroupDTO, PrayerRequestDTO
from aos.core.institution.service import InstitutionService
from aos.core.security.auth import get_current_operator, AosRole, requires_community_access

router = APIRouter(prefix="/institution", tags=["Institution"])
templates = Jinja2Templates(directory="aos/api/templates")

def get_institution_service() -> InstitutionService:
    from aos.api.state import institution_state
    if not institution_state.service:
        raise HTTPException(status_code=500, detail="Institution Service not initialized")
    return institution_state.service

def resolve_community_context(request: Request, operator: dict) -> Optional[str]:
    """
    Robustly resolves community_id from:
    1. Query Parameter (Highest priority)
    2. Persistent Cookie
    3. User Profile / Operator Identity
    
    Returns None if no valid context is found or explicitly cleared.
    """
    # 1. Check Query Parameter
    # Explicit community_id="" means "Reset/Force Selection"
    query_id = request.query_params.get("community_id")
    if query_id is not None:
        return query_id if query_id.strip() != "" else None

    # 2. Check Cookie
    cookie_id = request.cookies.get("aos_community_context")
    if cookie_id and cookie_id.strip():
        return cookie_id

    # 3. Check User Profile
    profile_id = operator.get("community_id")
    if profile_id and profile_id.strip():
        return profile_id

    return None

@router.get("/members", response_model=List[InstitutionMemberDTO])
async def get_members(
    community_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    """List all members for the Secretary/Admin."""
    all_members = service.members.list_all()
    return [m for m in all_members if m.community_id == community_id]

@router.post("/broadcast")
async def send_broadcast(
    community_id: str,
    message: str = Form(...),
    target: str = Form("ALL"),
    institution_type: str = "faith",
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Trigger a broadcast from the Dashboard."""
    operator_id = str(operator.get("id"))
    track_ids = await service.send_targeted_announcement(
        community_id, operator_id, target, message, institution_type
    )
    return {"status": "success", "recipients_count": len(track_ids)}

@router.post("/code/update")
async def update_registration_code(
    community_id: str = Form(...),
    custom_code: str = Form(""),
    code_active: str = Form(...),
    operator=Depends(get_current_operator)
):
    """Update registration code for a community."""
    from aos.api.state import community_state
    
    if community_state.module:
        group = community_state.module.get_group(community_id)
        if group:
            # Allow empty code when deactivating
            group.community_code = custom_code.strip().upper() if custom_code.strip() else None
            group.code_active = code_active.lower() == 'true'
            community_state.module._groups.save(group)
            return {"status": "success", "code": group.community_code}
    
    raise HTTPException(404, "Community not found")

@router.post("/attendance")
async def mark_attendance(
    community_id: str = Form(...),
    member_id: str = Form(...),
    service_type: str = Form(...),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Admin marks attendance."""
    success = service.mark_attendance(
        community_id=community_id, 
        member_id=member_id, 
        service_date=datetime.utcnow(), 
        service_type=service_type, 
        requester_id=str(operator.get("id"))
    )
    if not success:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"status": "success"}

@router.post("/members/add")
async def add_institution_member(
    community_id: str = Form(...),
    user_id: str = Form(...),
    channel: str = Form(...),
    institution_type: str = Form("faith"),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Add a member to both community_members and institution_members tables."""
    from aos.api.state import community_state
    from aos.db.models import InstitutionMemberDTO
    import uuid
    
    # Add to community_members first
    if community_state.module:
        try:
            community_state.module.add_member_to_community(
                community_id=community_id,
                user_id=user_id,
                channel=channel,
                actor_id=operator.get("sub")
            )
        except Exception as e:
            raise HTTPException(400, f"Failed to add to community: {str(e)}")
    
    # Add to institution_members
    try:
        member = InstitutionMemberDTO(
            id=str(uuid.uuid4()),
            community_id=community_id,
            institution_type=institution_type,
            full_name=user_id,
            role_id="member",
            joined_at=datetime.utcnow(),
            active=True
        )
        service.members.save(member)
        return {"status": "success", "member_id": member.id}
    except Exception as e:
        raise HTTPException(400, f"Failed to add to institution: {str(e)}")

@router.post("/members/update")
async def update_institution_member(
    member_id: str = Form(...),
    full_name: str = Form(...),
    role_id: str = Form(...),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Update member details."""
    # Find member by ID
    all_members = service.members.list_all()
    member = next((m for m in all_members if m.id == member_id), None)
    
    if not member:
        raise HTTPException(404, "Member not found")
    
    member.full_name = full_name
    member.role_id = role_id
    service.members.save(member)
    return {"status": "success"}

@router.post("/members/deactivate")
async def deactivate_institution_member(
    member_id: str = Form(...),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Deactivate member (soft delete)."""
    all_members = service.members.list_all()
    member = next((m for m in all_members if m.id == member_id), None)
    if not member:
        raise HTTPException(404, "Member not found")
    member.active = False
    service.members.save(member)
    return {"status": "success"}

@router.post("/members/delete")
async def delete_institution_member(
    member_id: str = Form(...),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Permanently delete member (hard delete)."""
    all_members = service.members.list_all()
    member = next((m for m in all_members if m.id == member_id), None)
    if not member:
        raise HTTPException(404, "Member not found")
    service.members.delete(member.id)
    return {"status": "success"}

@router.get("/analytics/trends")
async def get_trends(
    community_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    return service.get_attendance_trends(community_id)

@router.get("/finances")
async def get_finances(
    community_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    return service.get_financial_summary(community_id)

@router.post("/finances")
async def log_finance(
    community_id: str = Form(...),
    member_id: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    is_pledge: bool = Form(False),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    success = service.log_financial_entry(
        community_id=community_id, 
        amount=amount, 
        category=category, 
        entry_date=datetime.utcnow(),
        requester_id=str(operator.get("id")),
        member_id=member_id,
        is_pledge=is_pledge
    )
    if not success:
        raise HTTPException(403, "Unauthorized")
    return {"status": "success"}

@router.get("/export/{data_type}")
async def export_data(
    data_type: str,
    request: Request,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Export institutional data to CSV."""
    from aos.core.institution.export import InstitutionalExporter
    
    community_id = resolve_community_context(request, operator)
    if not community_id:
        raise HTTPException(400, "Community context required")
    
    if data_type == "members":
        data = [m for m in service.members.list_all() if m.community_id == community_id]
        content = InstitutionalExporter.members_to_csv(data)
    elif data_type == "attendance":
        data = [r for r in service.attendance.list_all() if r.community_id == community_id]
        content = InstitutionalExporter.attendance_to_csv(data)
    elif data_type == "finances":
        data = [e for e in service.finance.list_all() if e.community_id == community_id]
        content = InstitutionalExporter.finances_to_csv(data)
    elif data_type == "prayers":
        data = [p for p in service.prayers.list_all() if p.community_id == community_id]
        content = InstitutionalExporter.prayers_to_csv(data)
    else:
        raise HTTPException(status_code=400, detail="Invalid data type")
        
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={data_type}_{community_id}.csv"}
    )

@router.post("/groups", response_model=InstitutionGroupDTO)
async def create_group(
    community_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    institution_type: str = Form("faith"),
    service: InstitutionService = Depends(get_institution_service)
):
    return service.create_group(community_id, name, description, institution_type)

# --- UI ENDPOINTS ---

@router.get("/members/ui", response_class=HTMLResponse)
async def members_ui(
    request: Request,
    institution_type: str = "faith",
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Institutional Member Registry UI."""
    community_id = resolve_community_context(request, operator)
    
    # Selection Flow for Admins / Missing Context
    if not community_id:
        if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
            communities = service.communities.list_all()
            response = templates.TemplateResponse("institution_select_community.html", {
                "request": request,
                "user": operator,
                "communities": communities,
                "institution_type": institution_type,
                "target_url": "/institution/members/ui"
            })
            response.delete_cookie("aos_community_context")
            return response
        raise HTTPException(400, "Community context required. Please select a community.")
    
    # Get broadcast stats
    from aos.api.state import community_state
    broadcast_stats = {"pending": 0, "sent": 0, "failed": 0}
    invite_slug = None
    
    if community_state.module:
        # Get broadcast statistics
        status_res = community_state.module._db.execute("""
            SELECT d.status, COUNT(*) 
            FROM broadcast_deliveries d
            JOIN broadcasts b ON d.broadcast_id = b.id
            WHERE b.community_id = ?
            GROUP BY d.status
        """, (community_id,)).fetchall()
        
        for status, count in status_res:
            if status in broadcast_stats:
                broadcast_stats[status] = count
        
        # Get invite slug
        group = community_state.module.get_group(community_id)
        if group:
            invite_slug = group.invite_slug
        
    response_context = {
        "request": request,
        "user": operator,
        "members": [m for m in service.members.list_all() if m.community_id == community_id and (not m.institution_type or m.institution_type == institution_type)],
        "groups": [g for g in service.groups.list_all() if g.community_id == community_id and (not g.institution_type or g.institution_type == institution_type)],
        "community_id": community_id,
        "institution_type": institution_type,
        "labels": (service.get_plugin(institution_type).get_context_labels() if service.get_plugin(institution_type) else {}),
        "available_types": service.get_available_types(),
        "broadcast_stats": broadcast_stats,
        "invite_slug": invite_slug
    }
    
    response = templates.TemplateResponse("institution_members.html", response_context)
    # Sync Cookie for persistence
    if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
        response.set_cookie(key="aos_community_context", value=community_id, max_age=3600*24)
    return response

@router.get("/attendance/ui", response_class=HTMLResponse)
async def attendance_ui(
    request: Request,
    institution_type: str = "faith",
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Attendance Tracking UI."""
    community_id = resolve_community_context(request, operator)
    
    if not community_id:
        if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
            communities = service.communities.list_all()
            response = templates.TemplateResponse("institution_select_community.html", {
                "request": request,
                "user": operator,
                "communities": communities,
                "institution_type": institution_type,
                "target_url": "/institution/attendance/ui"
            })
            response.delete_cookie("aos_community_context")
            return response
        raise HTTPException(400, "Community context required")
        
    plugin = service.get_plugin(institution_type)
    response_context = {
        "request": request,
        "user": operator,
        "trends": service.get_attendance_trends(community_id),
        "members": [m for m in service.members.list_all() if m.community_id == community_id and (not m.institution_type or m.institution_type == institution_type)],
        "community_id": community_id,
        "institution_type": institution_type,
        "labels": (plugin.get_context_labels() if plugin else {}),
        "attendance_types": (plugin.get_attendance_types() if plugin else ["General"]),
        "available_types": service.get_available_types(),
        "now_date": datetime.now().strftime('%Y-%m-%d')
    }
    
    response = templates.TemplateResponse("institution_attendance.html", response_context)
    if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
        response.set_cookie(key="aos_community_context", value=community_id, max_age=3600*24)
    return response

@router.get("/finances/ui", response_class=HTMLResponse)
async def finances_ui(
    request: Request,
    institution_type: str = "faith",
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Financial Ledger UI."""
    community_id = resolve_community_context(request, operator)
    
    if not community_id:
        if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
            communities = service.communities.list_all()
            response = templates.TemplateResponse("institution_select_community.html", {
                "request": request,
                "user": operator,
                "communities": communities,
                "institution_type": institution_type,
                "target_url": "/institution/finances/ui"
            })
            response.delete_cookie("aos_community_context")
            return response
        raise HTTPException(400, "Community context required")
        
    plugin = service.get_plugin(institution_type)
    recent_entries = [e for e in service.finance.list_all() if e.community_id == community_id][-50:]
    recent_entries.reverse()

    response_context = {
        "request": request,
        "user": operator,
        "summary": service.get_financial_summary(community_id),
        "entries": recent_entries,
        "members": [m for m in service.members.list_all() if m.community_id == community_id and (not m.institution_type or m.institution_type == institution_type)],
        "community_id": community_id,
        "institution_type": institution_type,
        "labels": (plugin.get_context_labels() if plugin else {}),
        "financial_categories": (plugin.get_financial_categories() if plugin else ["General"]),
        "available_types": service.get_available_types()
    }
    
    response = templates.TemplateResponse("institution_finances.html", response_context)
    if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
        response.set_cookie(key="aos_community_context", value=community_id, max_age=3600*24)
    return response

@router.get("/prayers/ui", response_class=HTMLResponse)
async def prayers_ui(
    request: Request,
    institution_type: str = "faith",
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Prayer Request Review UI."""
    community_id = resolve_community_context(request, operator)
    
    if not community_id:
        if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
            communities = service.communities.list_all()
            response = templates.TemplateResponse("institution_select_community.html", {
                "request": request,
                "user": operator,
                "communities": communities,
                "institution_type": institution_type,
                "target_url": "/institution/prayers/ui"
            })
            response.delete_cookie("aos_community_context")
            return response
        raise HTTPException(400, "Community context required")
        
    response_context = {
        "request": request,
        "user": operator,
        "prayers": service.get_pending_prayers(community_id, str(operator.get("id"))),
        "community_id": community_id,
        "institution_type": institution_type,
        "labels": (service.get_plugin(institution_type).get_context_labels() if service.get_plugin(institution_type) else {}),
        "available_types": service.get_available_types()
    }
    
    response = templates.TemplateResponse("institution_prayers.html", response_context)
    if AosRole(operator.get("role", "viewer")).level >= AosRole.SYSTEM_ADMIN.level:
        response.set_cookie(key="aos_community_context", value=community_id, max_age=3600*24)
    return response

@router.get("/reports/weekly")
async def get_weekly_report(
    request: Request,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Generate and download the weekly PDF report."""
    community_id = resolve_community_context(request, operator)
    if not community_id:
        raise HTTPException(400, "Community context required")

    from aos.core.institution.reports import InstitutionalReportGenerator
    report_dir = "data/reports"
    report_path = os.path.join(report_dir, f"report_{community_id}_{datetime.now().strftime('%Y%m%d')}.pdf")
    
    generator = InstitutionalReportGenerator(service)
    try:
        pdf_path = await generator.generate_weekly_report(community_id, report_path)
        return FileResponse(
            pdf_path, 
            filename=f"Weekly_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(500, f"Report generation error: {str(e)}")
