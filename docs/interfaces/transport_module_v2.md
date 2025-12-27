# Transport Module v2 Interface Specification

**Status**: LOCKED  
**Effective Date**: 2025-12-28  
**Breaking Changes Require**: Staff Engineer Review + Migration Plan

---

## Overview

The Transport Module v2 provides Africa-first mobility intelligence infrastructure based on fluid zones, crowd-sourced traffic signals, and availability reporting. This specification locks the public API contract to prevent drift before scaling.

**Core Principle**: Local mobility intelligence without GPS or formal tracking. Zones replace routes, signals replace vehicle counts.

---

## Public Interface

### Zone Management

#### `register_zone`
```python
def register_zone(
    name: str,
    type: str,
    location_scope: Optional[str] = None
) -> str
```

**Purpose**: Register a new transport zone (road, stage, junction, area)  
**Returns**: Zone ID (UUID string)  
**Invariants**:
- `name` must be non-empty
- `type` in ["road", "stage", "junction", "area"]
- Returns unique zone_id for all operations

---

#### `discover_zones`
```python
def discover_zones(
    location_scope: Optional[str] = None,
    type_filter: Optional[str] = None
) -> List[TransportZoneDTO]
```

**Purpose**: Find transport zones by location or type  
**Returns**: Filtered list of zones  
**Invariants**:
- Location match is case-insensitive substring
- Type filter is exact match
- Returns all zones if no filters provided

---

#### `get_zone_intelligence`
```python
def get_zone_intelligence(zone_id: str) -> dict
```

**Purpose**: Aggregate recent signals and availability for a zone  
**Returns**: Intelligence dict with consensus state and confidence  
**Invariants**:
- Returns empty dict if zone not found
- Only includes non-expired signals and availability
- Calculates consensus state from confidence scores
- State priority: blocked > slow > flowing

**Return Schema**:
```python
{
    "zone_id": str,
    "zone_name": str,
    "type": str,
    "current_state": str,  # "flowing", "slow", "blocked", "unknown"
    "confidence": float,
    "signals": List[dict],  # Active traffic signals
    "availability": List[dict]  # Active availability reports
}
```

---

### Traffic Signal Reporting

#### `report_traffic_signal`
```python
def report_traffic_signal(
    zone_id: str,
    state: str,
    source: str,
    expires_in_minutes: int = 30
) -> bool
```

**Purpose**: Report traffic state for a zone  
**Returns**: True if successful, False if zone invalid  
**Invariants**:
- `zone_id` must reference existing zone
- `state` in ["flowing", "slow", "blocked"] (case-insensitive)
- `source` identifies reporter (user, agent, authority)
- Default expiry: 30 minutes
- `confidence_score` defaults to 1.0

---

### Availability Reporting

#### `report_availability`
```python
def report_availability(
    zone_id: str,
    destination: str,
    state: str,
    source: str,
    expires_in_minutes: int = 60
) -> bool
```

**Purpose**: Report vehicle availability to a destination from a zone  
**Returns**: True if successful, False if zone invalid  
**Invariants**:
- `zone_id` must reference existing zone
- `state` in ["available", "limited", "none"] (case-insensitive)
- `destination` is free-text (e.g., "Rongai", "CBD")
- Default expiry: 60 minutes

---

### Backward Compatibility Shims

#### `list_routes`
```python
def list_routes() -> List[Dict]
```

**Purpose**: Legacy shim mapping zones (type='road') to routes  
**Returns**: List of route-like dicts  
**Invariants**:
- Only returns zones with `type="road"`
- Maps to legacy format: `{id, name, start, end, price}`
- `start`, `end`, `price` are empty/zero (not used in v2)

---

#### `get_route_status`
```python
def get_route_status(route_id: str) -> Dict
```

**Purpose**: Legacy shim mapping zone intelligence to route status  
**Returns**: Route status dict  
**Invariants**:
- `route_id` is treated as `zone_id`
- Maps availability to "vehicles" for USSD compatibility
- Includes `traffic_state` from zone intelligence

**Return Schema**:
```python
{
    "route_id": str,
    "route_name": str,
    "vehicles": List[dict],  # Simulated from availability
    "traffic_state": str
}
```

---

## Data Transfer Objects (DTOs)

### TransportZoneDTO
```python
class TransportZoneDTO(BaseModel):
    id: str
    name: str
    type: str  # "road", "area", "stage", "junction"
    location_scope: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### TrafficSignalDTO
```python
class TrafficSignalDTO(BaseModel):
    id: str
    zone_id: str
    state: str  # "flowing", "slow", "blocked"
    source: str  # "user", "agent", "authority"
    confidence_score: float = 1.0
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
```

### TransportAvailabilityDTO
```python
class TransportAvailabilityDTO(BaseModel):
    id: str
    zone_id: str
    destination: str
    availability_state: str  # "available", "limited", "none"
    reported_by: str
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
```

---

## Design Invariants

### Invariant 1: Time-Based Expiry
- All signals and availability reports MUST have expiry timestamps
- Default: 30 minutes for traffic, 60 minutes for availability
- Expired data MUST NOT appear in zone intelligence

### Invariant 2: Consensus Calculation
- Zone state determined by aggregating confidence scores
- Multiple reports for same state increase confidence
- State priority: blocked > slow > flowing

### Invariant 3: Offline-First
- All data stored in SQLite with WAL mode
- No external API dependencies
- No GPS coordinates required

### Invariant 4: Human-Reported Intelligence
- Signals reported by users, agents, or authorities
- No automated vehicle tracking
- No formal route schedules

### Invariant 5: Fluid Infrastructure
- Zones are flexible (roads, stages, junctions, areas)
- No rigid route definitions
- No vehicle identity tracking

---

## Usage Patterns

### Pattern 1: Register and Discover Zones
```python
# Register zones
waiyaki_id = transport.register_zone(
    name="Waiyaki Way",
    type="road",
    location_scope="Westlands-CBD"
)

rongai_id = transport.register_zone(
    name="Rongai Stage",
    type="stage",
    location_scope="Rongai"
)

# Discover
roads = transport.discover_zones(type_filter="road")
westlands_zones = transport.discover_zones(location_scope="Westlands")
```

### Pattern 2: Report and Aggregate Traffic
```python
# Report traffic
transport.report_traffic_signal(
    zone_id=waiyaki_id,
    state="flowing",
    source="user-123"
)

transport.report_traffic_signal(
    zone_id=waiyaki_id,
    state="slow",
    source="user-456"
)

# Get intelligence (consensus)
intel = transport.get_zone_intelligence(waiyaki_id)
# intel["current_state"] = "flowing" (higher confidence)
# intel["confidence"] = 1.0
```

### Pattern 3: Report and Query Availability
```python
# Report availability
transport.report_availability(
    zone_id=rongai_id,
    destination="Rongai",
    state="available",
    source="agent-789"
)

# Get intelligence
intel = transport.get_zone_intelligence(rongai_id)
# intel["availability"] = [{"destination": "Rongai", "availability_state": "available", ...}]
```

### Pattern 4: Legacy USSD Compatibility
```python
# Legacy route listing
routes = transport.list_routes()
# Returns zones with type="road" in legacy format

# Legacy route status
status = transport.get_route_status(waiyaki_id)
# Returns zone intelligence mapped to legacy format
```

---

## Events Emitted

Currently, the Transport Module v2 does not emit domain events. Future versions may add:
- `TRANSPORT_ZONE_REGISTERED`
- `TRAFFIC_SIGNAL_REPORTED`
- `AVAILABILITY_REPORTED`

---

## Breaking Change Policy

**Any change to this interface requires**:
1. Staff Engineer review
2. Migration plan for existing clients
3. Deprecation period (minimum 1 release cycle)
4. Update to this specification version

**Examples of breaking changes**:
- Removing or renaming a public method
- Changing method signature (parameters, return type)
- Changing DTO field names or types
- Removing or changing invariants
- Changing state enums ("flowing", "slow", "blocked")

**Non-breaking changes**:
- Adding new optional parameters (with defaults)
- Adding new methods
- Adding new DTOs
- Adding new zone types
- Adding event emissions

---

## Migration Notes

### From v1 (Route/Vehicle Model)

**Deprecated Methods** (backward-compatible shims provided):
- `list_routes()` → Use `discover_zones(type_filter="road")`
- `get_route_status(route_id)` → Use `get_zone_intelligence(zone_id)`

**Migration Path**:
1. Existing routes auto-migrated to zones (type='road') via Migration 008
2. USSD/SMS adapters use shims for backward compatibility
3. New integrations should use v2 methods directly

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-28 | Initial locked specification for v2 (Africa-first model) |

---

**Signed**: FAANG Staff Engineer  
**Approved for**: Production Deployment
