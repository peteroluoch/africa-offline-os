"""
Sync Protocol
Defines message formats and protocol for peer-to-peer synchronization.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from aos.core.sync.vector_clock import VectorClock

@dataclass
class SyncChange:
    """Represents a single change to be synchronized."""
    entity_type: str  # "harvest", "farmer", "vehicle", etc.
    entity_id: str
    operation: str  # "create", "update", "delete"
    data: Dict[str, Any]
    vector_clock: VectorClock
    timestamp: int  # Unix timestamp
    node_id: str  # Originating node

@dataclass
class SyncRequest:
    """Request to synchronize with a peer."""
    from_node: str
    to_node: str
    last_sync_timestamp: int
    vector_clock: VectorClock
    request_id: str = field(default_factory=lambda: str(datetime.now(timezone.utc).timestamp()))

@dataclass
class SyncResponse:
    """Response containing changes to synchronize."""
    from_node: str
    to_node: str
    request_id: str
    changes: List[SyncChange]
    vector_clock: VectorClock
    success: bool = True
    error: Optional[str] = None

@dataclass
class SyncAck:
    """Acknowledgment of successful sync."""
    from_node: str
    to_node: str
    request_id: str
    applied_changes: int
    conflicts: int
    vector_clock: VectorClock
