"""
Institution API Router.
Exposes institutional operations to the Dashboard UI.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from aos.db.models import InstitutionMemberDTO, InstitutionGroupDTO, PrayerRequestDTO
from aos.core.institution.service import InstitutionService
from aos.api.dependencies import get_current_operator # Logic for admin access
# Note: In a real app, we'd inject the service. Here we assume global access or factory.

router = APIRouter(prefix="/institution", tags=["Institution"])

# This is a stub for service injection. 
# In the actual app, this would be initialized in app.py and passed via dependency.
def get_institution_service() -> InstitutionService:
    from aos.db.engine import get_connection
    from aos.db.repository import (
        InstitutionMemberRepository, InstitutionGroupRepository,
        InstitutionMessageLogRepository, PrayerRequestRepository,
        MemberVehicleMapRepository, CommunityGroupRepository,
        InstitutionGroupMemberRepository
    )
    conn = get_connection()
    return InstitutionService(
        member_repo=InstitutionMemberRepository(conn),
        group_repo=InstitutionGroupRepository(conn),
        msg_log_repo=InstitutionMessageLogRepository(conn),
        prayer_repo=PrayerRequestRepository(conn),
        vmap_repo=MemberVehicleMapRepository(conn),
        community_repo=CommunityGroupRepository(conn),
        group_member_repo=InstitutionGroupMemberRepository(conn)
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
