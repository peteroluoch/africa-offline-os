"""
Power Profiles and Policies
Defines power modes and their associated policies for resource conservation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PowerProfile(str, Enum):
    """Power profile modes based on battery level."""
    FULL_POWER = "FULL_POWER"
    BALANCED = "BALANCED"
    POWER_SAVER = "POWER_SAVER"
    CRITICAL = "CRITICAL"

@dataclass
class PowerPolicy:
    """Policy configuration for a power profile."""
    profile: PowerProfile

    # Background task intervals (seconds)
    background_sync_interval: int
    mesh_heartbeat_interval: int

    # Feature flags
    enable_ui_animations: bool
    enable_background_tasks: bool
    enable_mesh_sync: bool

    # Throttling
    max_concurrent_tasks: int
    log_level: str  # "DEBUG", "INFO", "WARNING", "ERROR"

# Default power policies
POWER_POLICIES = {
    PowerProfile.FULL_POWER: PowerPolicy(
        profile=PowerProfile.FULL_POWER,
        background_sync_interval=300,  # 5 minutes
        mesh_heartbeat_interval=60,    # 1 minute
        enable_ui_animations=True,
        enable_background_tasks=True,
        enable_mesh_sync=True,
        max_concurrent_tasks=10,
        log_level="INFO"
    ),

    PowerProfile.BALANCED: PowerPolicy(
        profile=PowerProfile.BALANCED,
        background_sync_interval=900,  # 15 minutes
        mesh_heartbeat_interval=120,   # 2 minutes
        enable_ui_animations=True,
        enable_background_tasks=True,
        enable_mesh_sync=True,
        max_concurrent_tasks=5,
        log_level="INFO"
    ),

    PowerProfile.POWER_SAVER: PowerPolicy(
        profile=PowerProfile.POWER_SAVER,
        background_sync_interval=1800,  # 30 minutes
        mesh_heartbeat_interval=300,    # 5 minutes
        enable_ui_animations=False,
        enable_background_tasks=False,  # Defer background tasks
        enable_mesh_sync=True,
        max_concurrent_tasks=3,
        log_level="WARNING"
    ),

    PowerProfile.CRITICAL: PowerPolicy(
        profile=PowerProfile.CRITICAL,
        background_sync_interval=0,     # Disabled
        mesh_heartbeat_interval=0,      # Disabled
        enable_ui_animations=False,
        enable_background_tasks=False,
        enable_mesh_sync=False,         # Store-and-forward only
        max_concurrent_tasks=1,
        log_level="ERROR"
    )
}

class PowerProfileManager:
    """
    Manages power profile transitions based on battery level.
    """

    def __init__(
        self,
        full_power_threshold: float = 80.0,
        balanced_threshold: float = 50.0,
        power_saver_threshold: float = 20.0,
        critical_threshold: float = 10.0
    ):
        self.full_power_threshold = full_power_threshold
        self.balanced_threshold = balanced_threshold
        self.power_saver_threshold = power_saver_threshold
        self.critical_threshold = critical_threshold

        self._current_profile = PowerProfile.FULL_POWER
        self._manual_override: PowerProfile | None = None

    def determine_profile(self, battery_percent: float) -> PowerProfile:
        """
        Determine appropriate power profile based on battery level.
        Uses hysteresis to prevent rapid switching.
        """
        # Manual override takes precedence
        if self._manual_override:
            return self._manual_override

        # Determine profile based on thresholds
        if battery_percent >= self.full_power_threshold:
            return PowerProfile.FULL_POWER
        elif battery_percent >= self.balanced_threshold:
            return PowerProfile.BALANCED
        elif battery_percent >= self.power_saver_threshold:
            return PowerProfile.POWER_SAVER
        else:
            return PowerProfile.CRITICAL

    def update_profile(self, battery_percent: float) -> tuple[PowerProfile, bool]:
        """
        Update current profile based on battery level.
        Returns: (new_profile, changed)
        """
        new_profile = self.determine_profile(battery_percent)
        changed = new_profile != self._current_profile

        if changed:
            self._current_profile = new_profile

        return new_profile, changed

    def get_current_profile(self) -> PowerProfile:
        """Get the current active power profile."""
        return self._current_profile

    def get_current_policy(self) -> PowerPolicy:
        """Get the policy for the current profile."""
        return POWER_POLICIES[self._current_profile]

    def set_manual_override(self, profile: PowerProfile | None):
        """
        Manually set power profile (for testing/debugging).
        Set to None to return to automatic mode.
        """
        self._manual_override = profile
        if profile:
            self._current_profile = profile

    def clear_manual_override(self):
        """Clear manual override and return to automatic mode."""
        self._manual_override = None
