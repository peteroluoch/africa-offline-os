from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path

from aos.core.config import settings


class AuditLogger:
    """
    Structured JSON Audit Logger for A-OS Security Events.
    Writes to a .jsonl file (JSON Lines) for disk-efficiency and atomic appending.
    """

    def __init__(self, log_file: str | None = None, max_size_mb: int = 10):
        if log_file:
            self.log_path = Path(log_file)
        else:
            # Default to data/logs/audit.jsonl
            log_dir = Path(settings.data_dir) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = log_dir / "audit.jsonl"
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def log_event(
        self,
        event_type: str,
        metadata: dict,
        severity: str = "INFO",
        correlation_id: str | None = None
    ) -> None:
        """
        Record a security event.
        """
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "severity": severity,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "metadata": metadata
        }

        # Ensure log directory exists (if not created in __init__)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        # Periodically check size and rotate if necessary
        if self.log_path.stat().st_size > self.max_size_bytes:
            self.rotate_logs()

    def rotate_logs(self) -> None:
        """Rotate audit logs (keep 3 old versions)."""
        import os
        for i in range(2, -1, -1):
            source = self.log_path if i == 0 else self.log_path.with_suffix(f".jsonl.{i}")
            dest = self.log_path.with_suffix(f".jsonl.{i+1}")
            if source.exists():
                if dest.exists():
                    os.remove(dest)
                os.rename(source, dest)
        logger = logging.getLogger("aos.security.audit")
        logger.info("Audit logs rotated.")

    def log_security_breach(self, details: dict, correlation_id: str | None = None) -> None:
        """Helper for high-severity security breaches."""
        self.log_event("SECURITY_BREACH", details, severity="CRITICAL", correlation_id=correlation_id)
