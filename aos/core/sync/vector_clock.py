"""
Vector Clock Implementation
Provides causality tracking for distributed sync across A-OS nodes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import json

@dataclass
class VectorClock:
    """
    Vector clock for tracking causality in distributed systems.
    Each node maintains a counter for itself and all known peers.
    """
    clocks: Dict[str, int] = field(default_factory=dict)
    
    def increment(self, node_id: str) -> None:
        """Increment the clock for a specific node."""
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1
    
    def update(self, other: 'VectorClock') -> None:
        """
        Update this clock with another clock (merge operation).
        Takes the maximum value for each node.
        """
        for node_id, count in other.clocks.items():
            self.clocks[node_id] = max(self.clocks.get(node_id, 0), count)
    
    def happens_before(self, other: 'VectorClock') -> bool:
        """
        Check if this clock happens before another clock.
        Returns True if all our counts <= other counts and at least one is strictly less.
        """
        if not self.clocks:
            return True
        
        all_less_or_equal = all(
            self.clocks.get(node_id, 0) <= other.clocks.get(node_id, 0)
            for node_id in self.clocks
        )
        
        at_least_one_less = any(
            self.clocks.get(node_id, 0) < other.clocks.get(node_id, 0)
            for node_id in self.clocks
        )
        
        return all_less_or_equal and at_least_one_less
    
    def concurrent_with(self, other: 'VectorClock') -> bool:
        """
        Check if this clock is concurrent with another (conflict).
        Returns True if neither happens before the other.
        """
        return not self.happens_before(other) and not other.happens_before(self)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.clocks)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VectorClock':
        """Deserialize from JSON string."""
        clocks = json.loads(json_str)
        return cls(clocks=clocks)
    
    def copy(self) -> 'VectorClock':
        """Create a deep copy of this clock."""
        return VectorClock(clocks=self.clocks.copy())
    
    def __repr__(self) -> str:
        return f"VectorClock({self.clocks})"


class ConflictResolutionStrategy:
    """Base class for conflict resolution strategies."""
    
    def resolve(self, local_value: any, remote_value: any, local_clock: VectorClock, remote_clock: VectorClock) -> any:
        """
        Resolve conflict between local and remote values.
        Returns the value to keep.
        """
        raise NotImplementedError


class LastWriteWins(ConflictResolutionStrategy):
    """
    Last-Write-Wins conflict resolution.
    Uses timestamp to determine which value to keep.
    """
    
    def resolve(self, local_value: any, remote_value: any, local_clock: VectorClock, remote_clock: VectorClock) -> any:
        """
        Compare timestamps and keep the latest.
        If timestamps are equal, use lexicographic comparison of node IDs.
        """
        # Assume values have 'updated_at' and 'node_id' attributes
        local_ts = getattr(local_value, 'updated_at', 0)
        remote_ts = getattr(remote_value, 'updated_at', 0)
        
        if local_ts > remote_ts:
            return local_value
        elif remote_ts > local_ts:
            return remote_value
        else:
            # Timestamps equal - use node ID as tiebreaker
            local_node = getattr(local_value, 'node_id', '')
            remote_node = getattr(remote_value, 'node_id', '')
            return local_value if local_node > remote_node else remote_value


class ManualResolution(ConflictResolutionStrategy):
    """
    Manual conflict resolution.
    Marks conflict for operator review.
    """
    
    def resolve(self, local_value: any, remote_value: any, local_clock: VectorClock, remote_clock: VectorClock) -> Optional[any]:
        """
        Return None to indicate manual resolution required.
        Conflict will be stored for operator review.
        """
        return None


@dataclass
class Conflict:
    """Represents an unresolved sync conflict."""
    id: str
    entity_type: str  # "harvest", "farmer", etc.
    entity_id: str
    local_value: any
    remote_value: any
    local_clock: VectorClock
    remote_clock: VectorClock
    created_at: int
    resolved: bool = False
    resolution: Optional[any] = None
