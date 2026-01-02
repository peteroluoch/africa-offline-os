"""
Institutional Export Service.
Handles CSV generation for member registries and other datasets.
"""
import csv
import io
from typing import List
from aos.db.models import InstitutionMemberDTO

class InstitutionalExporter:
    """
    Handles data exporting logic for the Secretary.
    """

    @staticmethod
    def members_to_csv(members: List[InstitutionMemberDTO]) -> str:
        """
        Exports a list of members to a CSV string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Member ID", "Full Name", "Role", "Joined At", "Active"])
        
        # Data
        for m in members:
            writer.writerow([
                m.id,
                m.full_name,
                m.role_id,
                m.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Yes" if m.active else "No"
            ])
            
        return output.getvalue()
