import os
import logging
from datetime import datetime, timedelta
from typing import Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

from aos.core.institution.service import InstitutionService

logger = logging.getLogger("aos.institution.reports")

class InstitutionalReportGenerator:
    """
    Generates deterministic PDF reports for institutional operations (Prompt 12).
    Covers Member Registry, Attendance, and Financials.
    """
    
    def __init__(self, service: InstitutionService):
        self.service = service
        self.styles = getSampleStyleSheet()

    async def generate_weekly_report(self, community_id: str, output_path: str) -> str:
        """Generates a weekly PDF summary."""
        # Ensure directory exists
        report_dir = os.path.dirname(output_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []

        # 1. Header
        elements.append(Paragraph(f"A-OS Institutional Report", self.styles['Title']))
        elements.append(Paragraph(f"Community ID: {community_id}", self.styles['Normal']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        elements.append(Spacer(1, 0.25 * inch))

        # 2. Member Statistics
        members = [m for m in self.service.members.list_all() if m.community_id == community_id]
        new_this_week = [m for m in members if (datetime.utcnow() - m.joined_at).days <= 7]
        
        elements.append(Paragraph("1. Member Statistics", self.styles['Heading2']))
        elements.append(Paragraph(f"Total Registered Members: {len(members)}", self.styles['Normal']))
        elements.append(Paragraph(f"New Members (Last 7 Days): {len(new_this_week)}", self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))

        # 3. Attendance Summary
        trends = self.service.get_attendance_trends(community_id)
        elements.append(Paragraph("2. Attendance Trends (Last 4 Weeks)", self.styles['Heading2']))
        
        if trends:
            data = [["Week Starting", "Attendance Count"]]
            for t in trends:
                data.append([t['week'], str(t['count'])])
            
            table = Table(data, hAlign='LEFT', colWidths=[2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No attendance data recorded in the last 4 weeks.", self.styles['Normal']))
        
        elements.append(Spacer(1, 0.2*inch))

        # 4. Financial Summary
        finance = self.service.get_financial_summary(community_id)
        elements.append(Paragraph("3. Financial Stewardship", self.styles['Heading2']))
        
        categories = finance.get("categories", [])
        if categories:
            f_data = [["Category", "Total Amount (KES)"]]
            total = 0
            for c in categories:
                amount = float(c['total'])
                f_data.append([c['category'].title(), f"{amount:,.2f}"])
                total += amount
            
            f_data.append(["TOTAL", f"{total:,.2f}"])
            
            f_table = Table(f_data, hAlign='LEFT', colWidths=[2*inch, 1.5*inch])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.black)
            ]))
            elements.append(f_table)
        else:
            elements.append(Paragraph("No financial transactions recorded for this period.", self.styles['Normal']))

        # 5. Audit Recap
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("Report generated securely from A-OS local node.", self.styles['Italic']))

        # Build PDF
        try:
            doc.build(elements)
            logger.info(f"Report generated successfully: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to build PDF report: {e}")
            raise
