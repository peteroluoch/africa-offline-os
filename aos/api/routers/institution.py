"""
Institution API Router.
Exposes institutional operations to the Dashboard UI.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from aos.db.models import InstitutionMemberDTO, InstitutionGroupDTO, PrayerRequestDTO
from aos.core.institution.service import InstitutionService
from aos.core.security.auth import get_current_operator

router = APIRouter(prefix="/institution", tags=["Institution"])

# This is a stub for service injection. 
# In the actual app, this would be initialized in app.py and passed via dependency.
def get_institution_service() -> InstitutionService:
    from aos.db.engine import get_connection
    from aos.db.repository import (
        InstitutionMemberRepository, InstitutionGroupRepository,
        InstitutionMessageLogRepository, PrayerRequestRepository,
        MemberVehicleMapRepository, CommunityGroupRepository,
        InstitutionGroupMemberRepository, InstitutionalAttendanceRepository,
        InstitutionalFinanceRepository
    )
    conn = get_connection()
    return InstitutionService(
        member_repo=InstitutionMemberRepository(conn),
        group_repo=InstitutionGroupRepository(conn),
        msg_log_repo=InstitutionMessageLogRepository(conn),
        prayer_repo=PrayerRequestRepository(conn),
        vmap_repo=MemberVehicleMapRepository(conn),
        community_repo=CommunityGroupRepository(conn),
        group_member_repo=InstitutionGroupMemberRepository(conn),
        attendance_repo=InstitutionalAttendanceRepository(conn),
        finance_repo=InstitutionalFinanceRepository(conn)
    )

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
    message: str,
    operator_id: str, # From auth
    service: InstitutionService = Depends(get_institution_service)
):
    """Trigger a broadcast from the Dashboard."""
    # Resolve operator to member identity
    # For now, we assume the operator maps to an ADMIN member.
    track_id = service.log_message(
        community_id, operator_id, "broadcast", "ALL", 
        "dashboard", "announcement", message
    )
    return {"status": "success", "tracking_id": track_id}

@router.post("/attendance")
async def mark_attendance(
    community_id: str,
    member_id: str,
    service_type: str,
    operator_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    """Admin marks attendance."""
    from datetime import datetime
    success = service.mark_attendance(community_id, member_id, datetime.utcnow(), service_type, operator_id)
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

@router.get("/prayers", response_model=List[PrayerRequestDTO])
async def get_prayers(
    community_id: str,
    operator_id: str,
    service: InstitutionService = Depends(get_institution_service)
):
    """Pastor reviews prayer requests."""
    return service.get_pending_prayers(community_id, operator_id)

@router.post("/groups", response_model=InstitutionGroupDTO)
async def create_group(
    community_id: str,
    name: str,
    description: str = None,
    service: InstitutionService = Depends(get_institution_service)
):
    """Admin creates a new institutional subgroup."""
    return service.create_group(community_id, name, description)
