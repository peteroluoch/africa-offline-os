from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from aos.core.security.audit import AuditLogger

if TYPE_CHECKING:
    from aos.core.resource.monitor import ResourceSnapshot

logger = logging.getLogger("aos.security.forensics")

class ForensicMonitor:
    """
    Proactive security and resource forensics.
    Triggers critical audit events when thresholds are breached.
    """
    
    def __init__(self, audit_logger: AuditLogger | None = None):
        self.audit = audit_logger or AuditLogger()
        self.thresholds = {
            "min_disk_mb": 100,
            "min_mem_percent": 5.0,
        }

    def check_health(self, snapshot: ResourceSnapshot) -> None:
        """Analyze snapshot and trigger alerts if dangerous levels reached."""
        
        # 1. Disk Space Forensic (Prevent SQLite corruption)
        if snapshot.disk_free_mb < self.thresholds["min_disk_mb"]:
            self.audit.log_event("RESOURCE_CRITICAL", {
                "type": "DISK_LOW",
                "value_mb": snapshot.disk_free_mb,
                "threshold": self.thresholds["min_disk_mb"]
            }, severity="CRITICAL")
            logger.error(f"[Forensics] DISK CRITICALLY LOW: {snapshot.disk_free_mb}MB")

        # 2. Memory Forensic
        if snapshot.memory_percent > (100 - self.thresholds["min_mem_percent"]):
            self.audit.log_event("RESOURCE_CRITICAL", {
                "type": "MEM_LOW",
                "value_percent": snapshot.memory_percent,
                "threshold_percent": 100 - self.thresholds["min_mem_percent"]
            }, severity="WARNING")
            logger.warning(f"[Forensics] RAM PRESSURE: {snapshot.memory_percent}%")

    def report_failed_login(self, username: str, ip: str | None = None) -> None:
        """Triggered on authentication failure."""
        self.audit.log_event("AUTH_FAILURE", {
            "username": username,
            "client_ip": ip or "unknown"
        }, severity="WARNING")

    def report_security_anomaly(self, event_type: str, details: dict) -> None:
        """Handle identified security anomalies."""
        self.audit.log_security_breach({
            "anomaly_type": event_type,
            **details
        })
