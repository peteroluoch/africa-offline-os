"""
Dependency Update Checker
Monitors self-hosted dependencies for updates and alerts admins.
FAANG-grade: Non-intrusive, admin-controlled, safe.
"""
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Dependencies to monitor
DEPENDENCIES = {
    "htmx": {
        "current": "1.9.10",
        "check_url": "https://api.github.com/repos/bigskysoftware/htmx/releases/latest",
        "changelog": "https://github.com/bigskysoftware/htmx/releases",
        "breaking_keywords": ["breaking", "migration", "deprecated"]
    },
    "inter_font": {
        "current": "3.0",
        "check_url": "https://api.github.com/repos/rsms/inter/releases/latest",
        "changelog": "https://github.com/rsms/inter/releases",
        "breaking_keywords": []
    }
}


def check_updates() -> List[Dict[str, Any]]:
    """
    Check for dependency updates.
    Returns list of available updates with metadata.
    Fails silently - never breaks the app.
    """
    updates = []
    
    for name, dep in DEPENDENCIES.items():
        try:
            response = requests.get(
                dep["check_url"],
                timeout=5,
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                latest = data.get("tag_name", "").lstrip("v")
                current = dep["current"]
                
                if latest and latest != current:
                    # Check for breaking changes
                    release_notes = data.get("body", "").lower()
                    has_breaking = any(
                        keyword in release_notes 
                        for keyword in dep["breaking_keywords"]
                    )
                    
                    updates.append({
                        "name": name.replace("_", " ").title(),
                        "current": current,
                        "latest": latest,
                        "changelog": dep["changelog"],
                        "breaking": has_breaking,
                        "severity": "warning" if has_breaking else "info"
                    })
                    
                    logger.info(f"Update available: {name} {current} → {latest}")
        
        except Exception as e:
            # Fail silently - don't break the app
            logger.debug(f"Failed to check {name} updates: {e}")
            continue
    
    return updates


def should_check_updates(last_check: datetime = None) -> bool:
    """
    Determine if we should check for updates.
    Check once per day to avoid rate limits.
    """
    if not last_check:
        return True
    
    return (datetime.now() - last_check) > timedelta(days=1)
