"""
Resource Management API Router
Endpoints for monitoring system resources and power profiles.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from aos.api.state import resource_state
from aos.core.security.auth import get_current_operator
from aos.core.resource import PowerProfile

router = APIRouter(prefix="/sys/resource", tags=["resource"])

@router.get("/status")
async def get_resource_status(current_user: dict = Depends(get_current_operator)):
    """Get current resource levels and power profile."""
    if not resource_state.manager:
        raise HTTPException(status_code=500, detail="ResourceManager not initialized")
    
    snapshot = resource_state.manager.get_snapshot()
    profile = resource_state.manager.get_current_profile()
    policy = resource_state.manager.get_current_policy()
    stats = resource_state.manager.get_scheduler_stats()
    
    if not snapshot:
        raise HTTPException(status_code=503, detail="No resource snapshot available yet")
    
    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "battery": {
            "percent": snapshot.battery.percent if snapshot.battery else 100.0,
            "status": snapshot.battery.status.value if snapshot.battery else "UNKNOWN",
            "plugged": snapshot.battery.plugged if snapshot.battery else True,
            "time_remaining": snapshot.battery.time_remaining if snapshot.battery else None
        } if snapshot.battery else None,
        "cpu_percent": snapshot.cpu_percent,
        "memory": {
            "percent": snapshot.memory_percent,
            "available_mb": snapshot.memory_available_mb
        },
        "disk": {
            "free_mb": snapshot.disk_free_mb,
            "percent": snapshot.disk_percent
        },
        "power_profile": profile.value,
        "policy": {
            "background_sync_interval": policy.background_sync_interval,
            "mesh_heartbeat_interval": policy.mesh_heartbeat_interval,
            "enable_ui_animations": policy.enable_ui_animations,
            "enable_background_tasks": policy.enable_background_tasks,
            "max_concurrent_tasks": policy.max_concurrent_tasks
        },
        "scheduler": stats
    }

@router.get("/profile")
async def get_power_profile(current_user: dict = Depends(get_current_operator)):
    """Get current power profile."""
    if not resource_state.manager:
        raise HTTPException(status_code=500, detail="ResourceManager not initialized")
    
    profile = resource_state.manager.get_current_profile()
    policy = resource_state.manager.get_current_policy()
    
    return {
        "profile": profile.value,
        "policy": {
            "background_sync_interval": policy.background_sync_interval,
            "mesh_heartbeat_interval": policy.mesh_heartbeat_interval,
            "enable_ui_animations": policy.enable_ui_animations,
            "enable_background_tasks": policy.enable_background_tasks,
            "max_concurrent_tasks": policy.max_concurrent_tasks
        }
    }

@router.post("/profile/{profile_name}")
async def set_power_profile(profile_name: str, current_user: dict = Depends(get_current_operator)):
    """Manually set power profile (for testing/debugging)."""
    if not resource_state.manager:
        raise HTTPException(status_code=500, detail="ResourceManager not initialized")
    
    try:
        profile = PowerProfile(profile_name.upper())
        resource_state.manager.set_manual_profile(profile)
        return {"status": "success", "profile": profile.value}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid profile: {profile_name}")

@router.delete("/profile/override")
async def clear_profile_override(current_user: dict = Depends(get_current_operator)):
    """Clear manual profile override and return to automatic mode."""
    if not resource_state.manager:
        raise HTTPException(status_code=500, detail="ResourceManager not initialized")
    
    resource_state.manager.set_manual_profile(None)
    profile = resource_state.manager.get_current_profile()
    return {"status": "success", "profile": profile.value, "mode": "automatic"}

@router.get("/tasks/deferred")
async def get_deferred_tasks(current_user: dict = Depends(get_current_operator)):
    """Get list of deferred tasks."""
    if not resource_state.manager:
        raise HTTPException(status_code=500, detail="ResourceManager not initialized")
    
    tasks = resource_state.manager.get_deferred_tasks()
    
    return {
        "count": len(tasks),
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "priority": task.priority.name,
                "state": task.state.value,
                "created_at": task.created_at.isoformat()
            }
            for task in tasks
        ]
    }
