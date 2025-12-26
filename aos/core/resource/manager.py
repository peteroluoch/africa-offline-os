"""
Resource Manager
Orchestrates resource monitoring, power profiles, and task scheduling.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from aos.core.resource.monitor import ResourceMonitor, ResourceSnapshot
from aos.core.resource.profiles import PowerProfile, PowerProfileManager
from aos.core.resource.scheduler import ResourceAwareScheduler, Task, TaskPriority
from aos.core.events import EventBus, Event

logger = logging.getLogger(__name__)

class ResourceManager:
    """
    Central resource management system.
    Monitors resources, manages power profiles, and schedules tasks.
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        check_interval: int = 30
    ):
        self.monitor = ResourceMonitor()
        self.profile_manager = PowerProfileManager()
        self.scheduler = ResourceAwareScheduler()
        self.event_bus = event_bus
        self.check_interval = check_interval
        
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        self._last_snapshot: Optional[ResourceSnapshot] = None
    
    async def start(self):
        """Start the resource manager background loop."""
        if self._running:
            logger.warning("ResourceManager already running")
            return
        
        self._running = True
        self._background_task = asyncio.create_task(self._monitoring_loop())
        logger.info("ResourceManager started")
    
    async def stop(self):
        """Stop the resource manager."""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        logger.info("ResourceManager stopped")
    
    async def _monitoring_loop(self):
        """Background loop for resource monitoring and profile updates."""
        while self._running:
            try:
                await self._check_resources()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_resources(self):
        """Check resources and update power profile if needed."""
        # Get current snapshot
        snapshot = self.monitor.get_snapshot()
        self._last_snapshot = snapshot
        
        # Update power profile based on battery
        battery_percent = snapshot.battery.percent if snapshot.battery else 100.0
        new_profile, changed = self.profile_manager.update_profile(battery_percent)
        
        if changed:
            logger.warning(f"Power profile changed to {new_profile.value} (Battery: {battery_percent:.1f}%)")
            
            # Publish profile change event
            if self.event_bus:
                await self.event_bus.publish(Event(
                    type="resource.power_profile_changed",
                    data={
                        "profile": new_profile.value,
                        "battery_percent": battery_percent,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                ))
        
        # Execute eligible tasks
        await self._execute_tasks()
    
    async def _execute_tasks(self):
        """Execute tasks that are eligible given current power profile."""
        current_profile = self.profile_manager.get_current_profile()
        policy = self.profile_manager.get_current_policy()
        
        # Execute up to max_concurrent_tasks
        executed = 0
        while executed < policy.max_concurrent_tasks:
            task = self.scheduler.execute_next(current_profile.value)
            if not task:
                break
            executed += 1
            
            logger.debug(f"Executed task: {task.name} (Priority: {task.priority.name})")
    
    def get_snapshot(self) -> Optional[ResourceSnapshot]:
        """Get the last resource snapshot."""
        return self._last_snapshot
    
    def get_current_profile(self) -> PowerProfile:
        """Get the current power profile."""
        return self.profile_manager.get_current_profile()
    
    def get_current_policy(self):
        """Get the current power policy."""
        return self.profile_manager.get_current_policy()
    
    def schedule_task(self, task: Task) -> str:
        """Schedule a task for execution."""
        return self.scheduler.schedule(task)
    
    def schedule_function(
        self,
        func,
        priority: TaskPriority = TaskPriority.NORMAL,
        name: str = "",
        *args,
        **kwargs
    ) -> str:
        """Schedule a function for execution."""
        return self.scheduler.schedule_function(func, priority, name, *args, **kwargs)
    
    def get_scheduler_stats(self) -> dict:
        """Get task scheduler statistics."""
        return self.scheduler.get_stats()
    
    def get_deferred_tasks(self) -> list[Task]:
        """Get list of deferred tasks."""
        return self.scheduler.get_deferred_tasks()
    
    def set_manual_profile(self, profile: Optional[PowerProfile]):
        """Manually set power profile (for testing)."""
        self.profile_manager.set_manual_override(profile)
        logger.info(f"Manual power profile override: {profile.value if profile else 'CLEARED'}")
