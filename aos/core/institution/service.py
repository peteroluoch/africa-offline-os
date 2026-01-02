"""
Institution Service - The "Brain" of A-OS.
Handles institutional business rules, member management, and cross-channel communication requests.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from aos.db.models import (
    InstitutionMemberDTO, InstitutionGroupDTO, InstitutionMessageLogDTO,
    PrayerRequestDTO, MemberVehicleMapDTO, InstitutionGroupMemberDTO,
    AttendanceRecordDTO, FinancialLedgerDTO
)
from aos.db.repository import (
    InstitutionMemberRepository, InstitutionGroupRepository,
    InstitutionMessageLogRepository, PrayerRequestRepository,
    MemberVehicleMapRepository, CommunityGroupRepository,
    InstitutionGroupMemberRepository, InstitutionalAttendanceRepository,
    InstitutionalFinanceRepository
)

logger = logging.getLogger("aos.institution")

class InstitutionService:
    """
    Orchestrates institutional logic. 
    Does not know about Telegram, SMS, or USSD.
    """

    def __init__(
        self,
        member_repo: InstitutionMemberRepository,
        group_repo: InstitutionGroupRepository,
        msg_log_repo: InstitutionMessageLogRepository,
        prayer_repo: PrayerRequestRepository,
        vmap_repo: MemberVehicleMapRepository,
        community_repo: CommunityGroupRepository,
        group_member_repo: InstitutionGroupMemberRepository,
        attendance_repo: InstitutionalAttendanceRepository,
        finance_repo: InstitutionalFinanceRepository
    ):
        self.members = member_repo
        self.groups = group_repo
        self.logs = msg_log_repo
        self.prayers = prayer_repo
        self.vmaps = vmap_repo
        self.communities = community_repo
        self.group_members = group_member_repo
        self.attendance = attendance_repo
        self.finance = finance_repo

    # --- Group Management (PROMPT 6) ---

    def create_group(self, community_id: str, name: str, description: str | None = None) -> InstitutionGroupDTO:
        """Create a new institutional subgroup."""
        group_id = str(uuid.uuid4())
        group = InstitutionGroupDTO(
            id=group_id,
            community_id=community_id,
            name=name,
            description=description
        )
        self.groups.save(group)
        return group

    def list_community_groups(self, community_id: str) -> list[InstitutionGroupDTO]:
        """List all groups within a community."""
        all_groups = self.groups.list_all()
        return [g for g in all_groups if g.community_id == community_id]

    def join_group(self, member_id: str, group_id: str) -> bool:
        """Join a member to a subgroup."""
        # Check if already joined
        existing = self.group_members.list_by_member(member_id)
        if any(m.group_id == group_id for m in existing):
            return True
        
        mapping = InstitutionGroupMemberDTO(
            id=str(uuid.uuid4()),
            group_id=group_id,
            member_id=member_id
        )
        self.group_members.save(mapping)
        return True

    def leave_group(self, member_id: str, group_id: str) -> bool:
        """Remove a member from a subgroup."""
        return self.group_members.delete_membership(group_id, member_id)

    def get_member_groups(self, member_id: str) -> list[InstitutionGroupDTO]:
        """Get all groups a member belongs to."""
        mappings = self.group_members.list_by_member(member_id)
        group_ids = [m.group_id for m in mappings]
        return [self.groups.get_by_id(gid) for gid in group_ids if self.groups.get_by_id(gid)]

    # --- Prayer Request Review (PROMPT 8) ---

    def get_pending_prayers(self, community_id: str, requester_id: str) -> list[PrayerRequestDTO]:
        """ADMIN/Pastor reviews pending prayer requests."""
        if not self.can_broadcast(requester_id): # Admin check
            return []
        
        all_prayers = self.prayers.list_all()
        return [p for p in all_prayers if p.community_id == community_id and p.status == "pending"]

    def update_prayer_status(self, prayer_id: str, status: str, requester_id: str) -> bool:
        """Update prayer status (e.g. shared, answered)."""
        if not self.can_broadcast(requester_id):
            return False
        
        prayer = self.prayers.get_by_id(prayer_id)
        if not prayer:
            return False
        
        prayer.status = status
        self.prayers.save(prayer)
        return True

    # --- Member Management ---

    def register_member(
        self, 
        community_id: str, 
        full_name: str, 
        vehicle_type: str, 
        vehicle_identity: str
    ) -> InstitutionMemberDTO:
        """
        Registers a new member and maps their vehicle identity.
        """
        # 1. Create Member (Brain)
        member_id = str(uuid.uuid4())
        member = InstitutionMemberDTO(
            id=member_id,
            community_id=community_id,
            full_name=full_name,
            role_id="MEMBER"
        )
        self.members.save(member)

        # 2. Map Vehicle (Adapter Layer)
        vmap = MemberVehicleMapDTO(
            id=str(uuid.uuid4()),
            member_id=member_id,
            vehicle_type=vehicle_type,
            vehicle_identity=vehicle_identity
        )
        self.vmaps.save(vmap)

        logger.info(f"Registered member {full_name} ({member_id}) via {vehicle_type}")
        return member

    def get_member_by_vehicle(self, vehicle_type: str, vehicle_identity: str) -> InstitutionMemberDTO | None:
        """Resolves a vehicle identity to a core member."""
        vmap = self.vmaps.get_by_vehicle(vehicle_type, vehicle_identity)
        if not vmap:
            return None
        return self.members.get_by_id(vmap.member_id)

    # --- Institutional Roles & RBAC (PROMPT 5) ---

    def can_broadcast(self, member_id: str) -> bool:
        """Only ADMIN (Pastor) can broadcast announcements."""
        member = self.members.get_by_id(member_id)
        return member is not None and member.role_id == "ADMIN"

    def can_manage_members(self, member_id: str) -> bool:
        """SECRETARY manages members."""
        member = self.members.get_by_id(member_id)
        return member is not None and member.role_id in ["ADMIN", "SECRETARY"]

    def can_access_finances(self, member_id: str) -> bool:
        """TREASURER accesses financial records."""
        member = self.members.get_by_id(member_id)
        return member is not None and member.role_id in ["ADMIN", "TREASURER"]

    def set_member_role(self, member_id: str, role_id: str, requester_id: str) -> bool:
        """
        Sets a member role if the requester has ADMIN privileges.
        """
        if not self.can_broadcast(requester_id): # Using ADMIN check
            logger.warning(f"Unauthorized role change attempt by {requester_id}")
            return False

        member = self.members.get_by_id(member_id)
        if not member:
            return False

        # Only allow defined roles
        if role_id not in ["ADMIN", "SECRETARY", "TREASURER", "MEMBER"]:
            return False

        member.role_id = role_id
        self.members.save(member)
        return True

    # --- Communication (The "Post Office" Logic) ---

    def log_message(
        self,
        community_id: str,
        sender_id: str,
        recipient_type: str,
        recipient_id: str,
        vehicle_type: str,
        message_type: str,
        content: str
    ) -> str:
        """
        Logs an outgoing message and returns a tracking ID.
        """
        msg_id = str(uuid.uuid4())
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        log = InstitutionMessageLogDTO(
            id=msg_id,
            community_id=community_id,
            sender_id=sender_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            vehicle_type=vehicle_type,
            message_type=message_type,
            content_hash=content_hash
        )
        self.logs.save(log)
        return msg_id

    # --- Module Logic (Prayer Requests) ---

    def submit_prayer_request(
        self,
        community_id: str,
        member_id: str,
        text: str,
        is_anonymous: bool = False
    ) -> PrayerRequestDTO:
        pr_id = str(uuid.uuid4())
        request = PrayerRequestDTO(
            id=pr_id,
            community_id=community_id,
            member_id=member_id,
            request_text=text,
            is_anonymous=is_anonymous
        )
        self.prayers.save(request)
        return request

    # --- Attendance Module (PROMPT 7) ---

    def mark_attendance(
        self,
        community_id: str,
        member_id: str,
        service_date: datetime,
        service_type: str,
        requester_id: str
    ) -> bool:
        """Admin marks member as present."""
        if not self.can_manage_members(requester_id):
            return False
            
        record = AttendanceRecordDTO(
            id=str(uuid.uuid4()),
            community_id=community_id,
            member_id=member_id,
            service_date=service_date,
            service_type=service_type
        )
        self.attendance.save(record)
        return True

    def get_attendance_trends(self, community_id: str) -> list[dict]:
        """Weekly attendance aggregates."""
        return self.attendance.get_weekly_trends(community_id)

    # --- Financial Ledger (PROMPT 8) ---

    def log_financial_entry(
        self,
        community_id: str,
        amount: float,
        category: str,
        entry_date: datetime,
        requester_id: str,
        member_id: str | None = None,
        is_pledge: bool = False,
        notes: str | None = None
    ) -> bool:
        """Log a tithe, offering, or pledge."""
        if not self.can_access_finances(requester_id):
            return False
            
        entry = FinancialLedgerDTO(
            id=str(uuid.uuid4()),
            community_id=community_id,
            member_id=member_id,
            amount=amount,
            category=category,
            is_pledge=is_pledge,
            entry_date=entry_date,
            notes=notes
        )
        self.finance.save(entry)
        return True

    def get_financial_summary(self, community_id: str) -> dict:
        """Consolidated report of categories and pledges."""
        return {
            "categories": self.finance.get_category_report(community_id),
            "pledges": self.finance.get_pledge_status(community_id)
        }

    # --- Institutional Analytics (PROMPT 6/10) ---

    def get_inactive_members(self, community_id: str, days: int = 30) -> list[InstitutionMemberDTO]:
        """
        Identify members who haven't attended any services in the last X days.
        Excludes ADMIN (Pastor) from the report.
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        all_members = [m for m in self.members.list_all() if m.community_id == community_id and m.role_id != "ADMIN"]
        
        inactive = []
        for member in all_members:
            # Check if any attendance after cutoff
            self.attendance.conn.row_factory = sqlite3.Row
            cursor = self.attendance.conn.execute(
                "SELECT id FROM institutional_attendance WHERE member_id = ? AND service_date > ? LIMIT 1",
                (member.id, cutoff)
            )
            if not cursor.fetchone():
                inactive.append(member)
        
        return inactive
