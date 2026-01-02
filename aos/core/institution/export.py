import csv
import io
from typing import List
from aos.db.models import (
    InstitutionMemberDTO, AttendanceRecordDTO, 
    FinancialLedgerDTO, PrayerRequestDTO
)

class InstitutionalExporter:
    """
    Handles data exporting logic for the Secretary (Data Sovereignty).
    """

    @staticmethod
    def members_to_csv(members: List[InstitutionMemberDTO]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Member ID", "Full Name", "Role", "Joined At", "Active"])
        for m in members:
            writer.writerow([m.id, m.full_name, m.role_id, m.joined_at, "Yes" if m.active else "No"])
        return output.getvalue()

    @staticmethod
    def attendance_to_csv(records: List[AttendanceRecordDTO]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Member ID", "Service Date", "Service Type", "Status"])
        for r in records:
            writer.writerow([r.id, r.member_id, r.service_date, r.service_type, r.status])
        return output.getvalue()

    @staticmethod
    def finances_to_csv(entries: List[FinancialLedgerDTO]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Member ID", "Amount", "Category", "Pledge", "Entry Date", "Notes"])
        for e in entries:
            writer.writerow([e.id, e.member_id or "Anonymous", e.amount, e.category, "Yes" if e.is_pledge else "No", e.entry_date, e.notes or ""])
        return output.getvalue()

    @staticmethod
    def prayers_to_csv(prayers: List[PrayerRequestDTO]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Member ID", "Request", "Anonymous", "Status", "Date"])
        for p in prayers:
            writer.writerow([p.id, p.member_id if not p.is_anonymous else "HIDDEN", p.request_text, "Yes" if p.is_anonymous else "No", p.status, p.created_at])
        return output.getvalue()
