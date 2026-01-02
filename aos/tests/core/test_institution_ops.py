import pytest
import sqlite3
import uuid
from datetime import datetime
from aos.db.models import CommunityGroupDTO, InstitutionMemberDTO, InstitutionGroupDTO
from aos.db.repository import (
    InstitutionMemberRepository, InstitutionGroupRepository,
    InstitutionMessageLogRepository, PrayerRequestRepository,
    MemberVehicleMapRepository, CommunityGroupRepository,
    InstitutionGroupMemberRepository, InstitutionalAttendanceRepository,
    InstitutionalFinanceRepository
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
        group_member_repo=InstitutionGroupMemberRepository(db_conn),
        attendance_repo=InstitutionalAttendanceRepository(db_conn),
        finance_repo=InstitutionalFinanceRepository(db_conn)
    )

@pytest.fixture
def router(service):
    # Register handlers
    r = CommandRouter(service)
    r.register_core("join", r.handle_join)
    r.register_core("myinfo", r.handle_myinfo)
    r.register_module("groups", r.handle_groups)
    r.register_module("join_group", r.handle_join_group)
    r.register_module("leave_group", r.handle_leave_group)
    r.register_module("broadcast", r.handle_broadcast)
    r.register_module("prayer", r.handle_prayer)
    r.register_module("prayer_list", r.handle_prayer_list)
    return r

@pytest.mark.asyncio
async def test_group_management_flow(router, service):
    # Setup
    comm = CommunityGroupDTO(id="comm_1", name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)
    
    # Create internal groups
    service.create_group("comm_1", "Choir", "Sunday singers")
    service.create_group("comm_1", "Youth", "Future leaders")

    # Member joins
    await router.handle_command("/join CHURCH1", "telegram", "user_1", user_name="Alice")
    
    # List groups
    groups_msg = await router.handle_command("/groups", "telegram", "user_1")
    assert "Choir" in groups_msg
    assert "Youth" in groups_msg

    # Join group
    join_res = await router.handle_command("/join_group Choir", "telegram", "user_1")
    assert "Successfully joined the Choir group" in join_res

    # Check myinfo
    info = await router.handle_command("/myinfo", "telegram", "user_1")
    assert "Groups: Choir" in info

    # Leave group
    leave_res = await router.handle_command("/leave_group Choir", "telegram", "user_1")
    assert "Left the Choir group" in leave_res

@pytest.mark.asyncio
async def test_broadcast_isolation(router, service):
    comm_id = "comm_1"
    comm = CommunityGroupDTO(id=comm_id, name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)

    # 1. Register Pastor (Admin)
    await router.handle_command("/join CHURCH1", "telegram", "pastor_1", user_name="Pastor John")
    pastor = service.get_member_by_vehicle("telegram", "pastor_1")
    raw_pastor = service.members.get_by_id(pastor.id)
    raw_pastor.role_id = "ADMIN"
    service.members.save(raw_pastor)

    # 2. Register Member
    await router.handle_command("/join CHURCH1", "telegram", "member_1", user_name="Member Alice")

    # 3. Member tries to broadcast
    fail_res = await router.handle_command("/broadcast Hello Church!", "telegram", "member_1")
    assert "Unauthorized" in fail_res

    # 4. Pastor broadcasts
    success_res = await router.handle_command("/broadcast Sunday service at 10am", "telegram", "pastor_1")
    assert "Broadcast queued" in success_res
    
    # 5. Verify log
    logs = service.logs.list_all()
    assert len(logs) == 1
    assert logs[0].message_type == "announcement"

@pytest.mark.asyncio
async def test_prayer_request_workflow(router, service):
    comm_id = "comm_1"
    comm = CommunityGroupDTO(id=comm_id, name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)

    # Pastor setup
    await router.handle_command("/join CHURCH1", "telegram", "pastor_1", user_name="Pastor John")
    pastor = service.get_member_by_vehicle("telegram", "pastor_1")
    raw_pastor = service.members.get_by_id(pastor.id)
    raw_pastor.role_id = "ADMIN"
    service.members.save(raw_pastor)

    # Member setup
    await router.handle_command("/join CHURCH1", "telegram", "member_1", user_name="Alice")

    # Member submits prayer
    await router.handle_command("/prayer Please pray for rain", "telegram", "member_1")

    # Pastor lists prayers
    prayer_list = await router.handle_command("/prayer_list", "telegram", "pastor_1")
    assert "Please pray for rain" in prayer_list

@pytest.mark.asyncio
async def test_attendance_and_inactive_report(router, service):
    comm_id = "comm_1"
    comm = CommunityGroupDTO(id=comm_id, name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)

    # Register Pastor
    await router.handle_command("/join CHURCH1", "telegram", "pastor_1", user_name="Pastor John")
    pastor = service.get_member_by_vehicle("telegram", "pastor_1")
    raw_pastor = service.members.get_by_id(pastor.id)
    raw_pastor.role_id = "ADMIN"
    service.members.save(raw_pastor)

    # Register member
    await router.handle_command("/join CHURCH1", "telegram", "m1", user_name="Attending Alice")
    m1 = service.get_member_by_vehicle("telegram", "m1")

    # Mark attendance for m1
    success = service.mark_attendance(comm_id, m1.id, datetime.utcnow(), "Sunday Morning", pastor.id)
    assert success == True

    # Verify attendance was recorded
    all_attendance = service.attendance.list_all()
    assert len(all_attendance) == 1
    assert all_attendance[0].member_id == m1.id

@pytest.mark.asyncio
async def test_financial_ledger_and_summary(router, service):
    comm_id = "comm_1"
    comm = CommunityGroupDTO(id=comm_id, name="Test Church", community_code="CHURCH1", code_active=True)
    service.communities.save(comm)

    # Register Pastor
    await router.handle_command("/join CHURCH1", "telegram", "pastor_1", user_name="Pastor John")
    pastor = service.get_member_by_vehicle("telegram", "pastor_1")
    raw_pastor = service.members.get_by_id(pastor.id)
    raw_pastor.role_id = "ADMIN"
    service.members.save(raw_pastor)

    # Log actual tithe
    service.log_financial_entry(comm_id, 1000.0, "tithe", datetime.utcnow(), pastor.id, is_pledge=False)
    # Log pledge
    service.log_financial_entry(comm_id, 5000.0, "building_fund", datetime.utcnow(), pastor.id, is_pledge=True)

    summary = service.get_financial_summary(comm_id)
    assert any(c["category"] == "tithe" and c["total"] == 1000.0 for c in summary["categories"])
    assert any(p["is_pledge"] == 1 and p["total"] == 5000.0 for p in summary["pledges"])

@pytest.mark.asyncio
async def test_export_sovereignty(service):
    from aos.core.institution.export import InstitutionalExporter
    from aos.db.models import InstitutionMemberDTO
    
    m1 = InstitutionMemberDTO(id="1", community_id="c1", full_name="Alice", role_id="MEMBER")
    csv_out = InstitutionalExporter.members_to_csv([m1])
    assert "Alice" in csv_out
    assert "Member ID" in csv_out
