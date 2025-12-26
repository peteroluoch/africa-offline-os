"""
Resource package initialization.
"""
from aos.core.resource.monitor import ResourceMonitor, ResourceSnapshot, BatteryInfo, BatteryStatus
from aos.core.resource.profiles import PowerProfile, PowerPolicy, PowerProfileManager, POWER_POLICIES
from aos.core.resource.scheduler import Task, TaskPriority, TaskState, ResourceAwareScheduler
from aos.core.resource.manager import ResourceManager
from aos.core.resource.power_aware import power_aware, should_run_task

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
