"""
Resource package initialization.
"""
from aos.core.resource.monitor import ResourceMonitor, ResourceSnapshot, BatteryInfo, BatteryStatus
from aos.core.resource.profiles import PowerProfile, PowerPolicy, PowerProfileManager, POWER_POLICIES
from aos.core.resource.scheduler import Task, TaskPriority, TaskState, ResourceAwareScheduler
from aos.core.resource.manager import ResourceManager

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
]
