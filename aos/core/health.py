"""
Health Monitoring Module - TASK 0.3
Comprehensive health checks for production infrastructure (100M+ scale).

Provides:
- Disk space monitoring (critical for edge devices)
- Power-safe uptime tracking
- Database health status
"""
from __future__ import annotations

import shutil
import sqlite3
import time
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HealthStatus:
    """
    Comprehensive health status for A-OS kernel.
    
    Attributes:
        status: Overall system status
        disk_free_mb: Available disk space in megabytes
        uptime_seconds: System uptime (power-safe, persisted)
        db_status: Database health status
    """

    status: str = "ok"
    disk_free_mb: float = 0.0
    uptime_seconds: float = 0.0
    db_status: Literal["healthy", "degraded", "unavailable"] = "healthy"
    # Kernel Performance Metrics (Phase 4)
    events_processed: int = 0
    avg_latency_ms: float = 0.0


def get_disk_space(path: str = ".") -> float:
    """
    Get available disk space in megabytes.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        Available space in MB
    """
    usage = shutil.disk_usage(path)
    return usage.free / (1024 * 1024)  # Convert bytes to MB


def get_uptime(start_time: float | None = None) -> float:
    """
    Get system uptime in seconds.
    
    Args:
        start_time: Boot timestamp (if None, returns 0)
        
    Returns:
        Uptime in seconds
    """
    if start_time is None:
        return 0.0
    return time.time() - start_time


def check_db_health(conn: sqlite3.Connection | None) -> Literal["healthy", "degraded", "unavailable"]:
    """
    Check database health status.
    
    Args:
        conn: SQLite connection to check
        
    Returns:
        Health status: healthy, degraded, or unavailable
    """
    if conn is None:
        return "unavailable"

    try:
        # Check if connection is alive
        conn.execute("SELECT 1")

        # Check WAL mode (critical for power-loss safety)
        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()

        if mode and mode[0].lower() == "wal":
            return "healthy"
        else:
            return "degraded"  # WAL mode disabled

    except sqlite3.Error:
        return "unavailable"
