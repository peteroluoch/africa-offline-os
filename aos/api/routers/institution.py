from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from typing import List
from datetime import datetime

from aos.db.models import InstitutionMemberDTO, InstitutionGroupDTO, PrayerRequestDTO
from aos.core.institution.service import InstitutionService
from aos.core.security.auth import get_current_operator, AosRole, requires_community_access

router = APIRouter(prefix="/institution", tags=["Institution"])
templates = Jinja2Templates(directory="aos/api/templates")

# This is a stub for service injection. 
# In the actual app, this would be initialized in app.py and passed via dependency.
def get_institution_service() -> InstitutionService:
    from aos.api.state import institution_state
    if not institution_state.service:
        raise HTTPException(status_code=500, detail="Institution Service not initialized")
    return institution_state.service

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
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Trigger a broadcast from the Dashboard."""
    # Resolve operator to member identity
    operator_id = str(operator.get("id"))
    
    track_ids = await service.send_targeted_announcement(
        community_id, operator_id, target, message
    )
    
    return {
        "status": "success",
        "recipients_count": len(track_ids),
        "tracking_ids": track_ids
    }

@router.post("/attendance")
async def mark_attendance(
    community_id: str = Form(...),
    member_id: str = Form(...),
    service_type: str = Form(...),
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Admin marks attendance."""
    from datetime import datetime
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

@router.get("/analytics/trends")
async def get_trends(
    community_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    """Weekly attendance trends."""
    return service.get_attendance_trends(community_id)

@router.get("/finances")
async def get_finances(
    community_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    """Financial summary."""
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
    """Log a financial entry."""
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

@router.get("/analytics/inactive")
async def get_inactive(
    community_id: str,
    days: int = 30,
    service: InstitutionService = Depends(get_institution_service)
):
    """List members inactive for X days."""
    return service.get_inactive_members(community_id, days)

@router.get("/export/{data_type}")
async def export_data(
    data_type: str,
    community_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    """Export institutional data to CSV."""
    from aos.core.institution.export import InstitutionalExporter
    
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
        
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={data_type}_{community_id}.csv"}
    )

@router.post("/prayers/{request_id}/review")
async def review_prayer(
    request_id: str,
    community_id: str,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Mark a prayer request as reviewed."""
    success = service.update_prayer_status(
        prayer_id=request_id,
        status="shared", 
        requester_id=str(operator.get("id"))
    )
    if not success:
        raise HTTPException(403, "Unauthorized")
    return {"status": "success"}

@router.post("/groups", response_model=InstitutionGroupDTO)
async def create_group(
    community_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    service: InstitutionService = Depends(get_institution_service)
):
    """Admin creates a new institutional subgroup."""
    return service.create_group(community_id, name, description)

# --- UI ENDPOINTS ---

@router.get("/members/ui", response_class=HTMLResponse)
async def members_ui(
    request: Request,
    community_id: str = None,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Institutional Member Registry UI."""
    # RBAC: Enforce community context
    if not community_id:
        community_id = operator.get("community_id")
    
    if not community_id:
        raise HTTPException(400, "Community context required")
        
    members = [m for m in service.members.list_all() if m.community_id == community_id]
    groups = [g for g in service.groups.list_all() if g.community_id == community_id]
    
    return templates.TemplateResponse("institution_members.html", {
        "request": request,
        "user": operator,
        "members": members,
        "groups": groups,
        "community_id": community_id
    })

@router.get("/attendance/ui", response_class=HTMLResponse)
async def attendance_ui(
    request: Request,
    community_id: str = None,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Attendance Tracking UI."""
    if not community_id:
        community_id = operator.get("community_id")
        
    if not community_id:
        raise HTTPException(400, "Community context required")
        
    trends = service.get_attendance_trends(community_id)
    members = [m for m in service.members.list_all() if m.community_id == community_id]
    
    return templates.TemplateResponse("institution_attendance.html", {
        "request": request,
        "user": operator,
        "trends": trends,
        "members": members,
        "community_id": community_id,
        "now_date": datetime.now().strftime('%Y-%m-%d')
    })

@router.get("/finances/ui", response_class=HTMLResponse)
async def finances_ui(
    request: Request,
    community_id: str = None,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Financial Ledger UI."""
    if not community_id:
        community_id = operator.get("community_id")
        
    if not community_id:
        raise HTTPException(400, "Community context required")
        
    summary = service.get_financial_summary(community_id)
    # Get recent entries
    recent_entries = [e for e in service.finance.list_all() if e.community_id == community_id][-50:]
    recent_entries.reverse()
    
    # Get members for dropdown
    members = [m for m in service.members.list_all() if m.community_id == community_id]
    
    return templates.TemplateResponse("institution_finances.html", {
        "request": request,
        "user": operator,
        "summary": summary,
        "entries": recent_entries,
        "members": members,
        "community_id": community_id
    })

@router.get("/prayers/ui", response_class=HTMLResponse)
async def prayers_ui(
    request: Request,
    community_id: str = None,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Prayer Request Review UI."""
    if not community_id:
        community_id = operator.get("community_id")
        
    if not community_id:
        raise HTTPException(400, "Community context required")
        
    prayers = service.get_pending_prayers(community_id, str(operator.get("id")))
    
    return templates.TemplateResponse("institution_prayers.html", {
        "request": request,
        "user": operator,
        "prayers": prayers,
        "community_id": community_id
    })

@router.get("/reports/weekly")
async def get_weekly_report(
    community_id: str = None,
    operator=Depends(get_current_operator),
    service: InstitutionService = Depends(get_institution_service)
):
    """Generate and download the weekly PDF report."""
    from aos.core.institution.reports import InstitutionalReportGenerator
    
    if not community_id:
        community_id = operator.get("community_id")
    
    if not community_id:
        raise HTTPException(400, "Community context required")

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
