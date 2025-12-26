"""
Resource Monitoring Infrastructure
Platform-agnostic resource monitoring for battery, CPU, memory, and disk.
"""
from __future__ import annotations

import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

import psutil


class BatteryStatus(str, Enum):
    """Battery charging status."""
    CHARGING = "CHARGING"
    DISCHARGING = "DISCHARGING"
    FULL = "FULL"
    UNKNOWN = "UNKNOWN"

@dataclass
class BatteryInfo:
    """Battery information snapshot."""
    percent: float  # 0-100
    status: BatteryStatus
    plugged: bool
    time_remaining: int | None = None  # seconds, None if unknown

@dataclass
class ResourceSnapshot:
    """Complete resource snapshot at a point in time."""
    timestamp: datetime
    battery: BatteryInfo | None
    cpu_percent: float
    memory_percent: float
    memory_available_mb: int
    disk_free_mb: int
    disk_percent: float

class ResourceMonitor:
    """
    Platform-agnostic resource monitor.
    Uses psutil for cross-platform compatibility.
    """

    def __init__(self):
        self.platform = platform.system()
        self._last_snapshot: ResourceSnapshot | None = None

    def get_battery_info(self) -> BatteryInfo | None:
        """
        Get current battery information.
        Returns None if no battery is present (desktop).
        """
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return None

            # Determine status
            if battery.power_plugged:
                status = BatteryStatus.FULL if battery.percent >= 99 else BatteryStatus.CHARGING
            else:
                status = BatteryStatus.DISCHARGING

            return BatteryInfo(
                percent=battery.percent,
                status=status,
                plugged=battery.power_plugged,
                time_remaining=battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            )
        except Exception:
            # Battery info not available on this platform
            return None

    def get_cpu_percent(self, interval: float = 0.1) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=interval)

    def get_memory_info(self) -> tuple[float, int]:
        """
        Get memory information.
        Returns: (percent_used, available_mb)
        """
        mem = psutil.virtual_memory()
        return mem.percent, mem.available // (1024 * 1024)

    def get_disk_info(self) -> tuple[int, float]:
        """
        Get disk information for root partition.
        Returns: (free_mb, percent_used)
        """
        disk = psutil.disk_usage('/')
        return disk.free // (1024 * 1024), disk.percent

    def get_snapshot(self) -> ResourceSnapshot:
        """Get a complete resource snapshot."""
        battery = self.get_battery_info()
        cpu_percent = self.get_cpu_percent()
        memory_percent, memory_available_mb = self.get_memory_info()
        disk_free_mb, disk_percent = self.get_disk_info()

        snapshot = ResourceSnapshot(
            timestamp=datetime.now(UTC),
            battery=battery,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            disk_free_mb=disk_free_mb,
            disk_percent=disk_percent
        )

        self._last_snapshot = snapshot
        return snapshot

    def get_last_snapshot(self) -> ResourceSnapshot | None:
        """Get the last recorded snapshot without taking a new one."""
        return self._last_snapshot

    def is_on_battery(self) -> bool:
        """Check if system is running on battery power."""
        battery = self.get_battery_info()
        if battery is None:
            return False  # No battery = assume plugged in
        return not battery.plugged

    def get_battery_percent(self) -> float:
        """
        Get battery percentage.
        Returns 100.0 if no battery (desktop).
        """
        battery = self.get_battery_info()
        return battery.percent if battery else 100.0
