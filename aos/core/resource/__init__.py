"""
Resource package initialization.
"""
from aos.core.resource.manager import ResourceManager
from aos.core.resource.monitor import BatteryInfo, BatteryStatus, ResourceMonitor, ResourceSnapshot
from aos.core.resource.power_aware import power_aware, should_run_task
from aos.core.resource.profiles import (
    POWER_POLICIES,
    PowerPolicy,
    PowerProfile,
    PowerProfileManager,
)
from aos.core.resource.scheduler import ResourceAwareScheduler, Task, TaskPriority, TaskState

__all__ = [
    "ResourceMonitor",
    "ResourceSnapshot",
    "BatteryInfo",
    "BatteryStatus",
    "PowerProfile",
    "PowerPolicy",
    "PowerProfileManager",
    "POWER_POLICIES",
    "Task",
    "TaskPriority",
    "TaskState",
    "ResourceAwareScheduler",
    "ResourceManager",
    "power_aware",
    "should_run_task",
]
