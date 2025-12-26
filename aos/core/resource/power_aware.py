"""
Power-Aware Decorator
Automatically defers function execution based on power profile.
"""
from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aos.core.resource.manager import ResourceManager
    from aos.core.resource.profiles import PowerProfile

logger = logging.getLogger(__name__)

def power_aware(min_profile: PowerProfile):
    """
    Decorator that defers function execution if power profile is too low.
    
    Args:
        min_profile: Minimum power profile required to execute function
        
    Usage:
        @power_aware(min_profile=PowerProfile.BALANCED)
        async def background_task(self):
            # Only runs if profile >= BALANCED
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check if instance has resource_manager
            resource_manager: ResourceManager | None = getattr(self, 'resource_manager', None)

            if not resource_manager:
                # No resource manager = always execute
                return await func(self, *args, **kwargs)

            current_profile = resource_manager.get_current_profile()

            # Import here to avoid circular dependency
            from aos.core.resource.profiles import PowerProfile

            # Define profile priority (lower number = higher priority/more power available)
            profile_priority = {
                PowerProfile.FULL_POWER: 0,
                PowerProfile.BALANCED: 1,
                PowerProfile.POWER_SAVER: 2,
                PowerProfile.CRITICAL: 3
            }

            current_priority = profile_priority.get(current_profile, 999)
            min_priority = profile_priority.get(min_profile, 0)

            if current_priority <= min_priority:
                # Sufficient power - execute
                return await func(self, *args, **kwargs)
            else:
                # Insufficient power - defer
                logger.info(
                    f"Deferring {func.__name__} due to {current_profile.value} power mode "
                    f"(requires {min_profile.value})"
                )
                return None

        return wrapper
    return decorator

def should_run_task(
    resource_manager: ResourceManager | None,
    task_name: str,
    min_profile: PowerProfile
) -> bool:
    """
    Helper function to check if a task should run given current power profile.
    
    Args:
        resource_manager: ResourceManager instance (optional)
        task_name: Name of task for logging
        min_profile: Minimum profile required
        
    Returns:
        True if task should run, False if should be deferred
    """
    if not resource_manager:
        return True

    current_profile = resource_manager.get_current_profile()

    # Import here to avoid circular dependency
    from aos.core.resource.profiles import PowerProfile

    profile_priority = {
        PowerProfile.FULL_POWER: 0,
        PowerProfile.BALANCED: 1,
        PowerProfile.POWER_SAVER: 2,
        PowerProfile.CRITICAL: 3
    }

    current_priority = profile_priority.get(current_profile, 999)
    min_priority = profile_priority.get(min_profile, 0)

    if current_priority <= min_priority:
        return True

    logger.info(
        f"Deferring {task_name} due to {current_profile.value} power mode "
        f"(requires {min_profile.value})"
    )
    return False
