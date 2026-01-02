import pytest
import sqlite3
import uuid
from aos.db.models import CommunityGroupDTO
from aos.db.repository import (
    InstitutionMemberRepository, InstitutionGroupRepository,
    InstitutionMessageLogRepository, PrayerRequestRepository,
    MemberVehicleMapRepository, CommunityGroupRepository,
    InstitutionGroupMemberRepository
)
from aos.core.institution.service import InstitutionService
from aos.core.vehicles.router import CommandRouter

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    from aos.db.migrations import MigrationManager
    from aos.db.migrations.registry import MIGRATIONS
    
    manager = MigrationManager(conn)
    manager.apply_migrations(MIGRATIONS)
    
    return conn

@pytest.fixture
def service(db_conn):
    return InstitutionService(
        member_repo=InstitutionMemberRepository(db_conn),
        group_repo=InstitutionGroupRepository(db_conn),
        msg_log_repo=InstitutionMessageLogRepository(db_conn),
        prayer_repo=PrayerRequestRepository(db_conn),
        vmap_repo=MemberVehicleMapRepository(db_conn),
        community_repo=CommunityGroupRepository(db_conn),
        group_member_repo=InstitutionGroupMemberRepository(db_conn)
    )

@pytest.fixture
def router(service):
    return CommandRouter(service)

def test_member_registration_and_identity_mapping(service):
    # setup community
    comm = CommunityGroupDTO(id="comm_1", name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)

    # register
    member = service.register_member("comm_1", "John Doe", "telegram", "12345")
    
    assert member.full_name == "John Doe"
    assert member.role_id == "MEMBER"
    
    # lookup
    resolved = service.get_member_by_vehicle("telegram", "12345")
    assert resolved is not None
    assert resolved.id == member.id
    assert resolved.full_name == "John Doe"

def test_rbac_enforcement(service):
    comm_id = "comm_1"
    # Admin
    admin = service.register_member(comm_id, "Pastor", "telegram", "admin_1")
    service.set_member_role(admin.id, "ADMIN", admin.id) # Self-set for test setup or bypass logic? 
    # Actually set_member_role requires requester to be ADMIN. 
    # Let's bypass for test setup.
    raw_admin = service.members.get_by_id(admin.id)
    raw_admin.role_id = "ADMIN"
    service.members.save(raw_admin)

    # Secretary
    sec = service.register_member(comm_id, "Sec", "telegram", "sec_1")
    service.set_member_role(sec.id, "SECRETARY", admin.id)

    # Checks
    assert service.can_broadcast(admin.id) is True
    assert service.can_broadcast(sec.id) is False
    assert service.can_manage_members(sec.id) is True
    assert service.can_access_finances(sec.id) is False

@pytest.mark.asyncio
async def test_command_routing(router, service):
    # Setup
    comm = CommunityGroupDTO(id="comm_1", name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)
    
    # Register Core handlers in router
    router.register_core("join", router.handle_join)
    router.register_core("myinfo", router.handle_myinfo)

    # 1. Join
    response = await router.handle_command("/join CHURCH1", "telegram", "user_1", user_name="Alice")
    assert "Successfully joined Test Church" in response

    # 2. MyInfo
    info = await router.handle_command("/myinfo", "telegram", "user_1")
    assert "Alice" in info
    assert "MEMBER" in info

    # 3. Unknown
    unknown = await router.handle_command("/unknown", "telegram", "user_1")
    assert "Unknown command" in unknown
