# Community Module Interface Specification v1.0

**Status**: LOCKED  
**Effective Date**: 2025-12-28  
**Breaking Changes Require**: Staff Engineer Review + Migration Plan

---

## Overview

The Community Module provides infrastructure-first social distribution for trusted local organizations (churches, mosques, committees). This specification locks the public API contract to prevent drift before scaling.

**Core Principle**: Groups hold accounts, not individuals. Zero individual authentication required.

---

## Public Interface

### Group Management

#### `register_group`
```python
async def register_group(
    name: str,
    tags: List[str],
    location: str,
    admin_id: str,
    preferred_channels: str = "ussd,sms",
    group_type: str = "",
    description: str = ""
) -> CommunityGroupDTO
```

**Purpose**: Register a new community group  
**Returns**: Newly created group DTO  
**Raises**: `ValueError` if validation fails  
**Invariants**:
- `name` must be non-empty
- `admin_id` must reference valid operator
- `tags` stored as JSON array
- `location` required for discovery

---

#### `get_group`
```python
def get_group(group_id: str) -> Optional[CommunityGroupDTO]
```

**Purpose**: Retrieve group by ID  
**Returns**: Group DTO or None  
**Invariants**: None

---

#### `list_groups`
```python
def list_groups() -> List[CommunityGroupDTO]
```

**Purpose**: List all registered groups  
**Returns**: List of all groups (active and inactive)  
**Invariants**: None

---

#### `discover_groups`
```python
def discover_groups(
    location: Optional[str] = None,
    tag_filter: Optional[List[str]] = None
) -> List[CommunityGroupDTO]
```

**Purpose**: Discover groups by location and/or tags  
**Returns**: Filtered list of active groups only  
**Invariants**:
- Only returns `active=True` groups
- Location match is case-insensitive substring
- Tag match is case-insensitive any-match

---

### Event Management

#### `publish_event`
```python
async def publish_event(
    group_id: str,
    title: str,
    event_type: str,
    start_time: datetime,
    end_time: Optional[datetime] = None,
    recurrence: Optional[str] = None,
    visibility: str = "public",
    language: str = "en"
) -> CommunityEventDTO
```

**Purpose**: Publish an event for a group  
**Returns**: Newly created event DTO  
**Raises**: `ValueError` if group_id invalid  
**Invariants**:
- `group_id` must reference existing group
- `start_time` required
- `visibility` in ["public", "members"]
- Emits `COMMUNITY_EVENT_CREATED` event

---

#### `list_events`
```python
def list_events(
    group_id: Optional[str] = None,
    event_type: Optional[str] = None,
    date: Optional[datetime] = None
) -> List[CommunityEventDTO]
```

**Purpose**: List events with optional filters  
**Returns**: Filtered list of events  
**Invariants**:
- If `group_id` provided, only returns events for that group
- If `date` provided, only returns events on that date
- If `event_type` provided, filters by type

---

### Announcement & Broadcasting

#### `publish_announcement`
```python
async def publish_announcement(
    group_id: str,
    message: str,
    urgency: str = "normal",
    expires_at: Optional[datetime] = None,
    target_audience: str = "public"
) -> CommunityAnnouncementDTO
```

**Purpose**: Publish an announcement for a group  
**Returns**: Newly created announcement DTO  
**Raises**: `ValueError` if group_id invalid  
**Invariants**:
- `group_id` must reference existing group
- `urgency` in ["normal", "urgent"]
- `target_audience` in ["public", "members"]
- Emits `COMMUNITY_ANNOUNCEMENT_CREATED` event

---

### Member Management (SECURITY-CRITICAL)

#### `add_member_to_community`
```python
def add_member_to_community(
    community_id: str,
    user_id: str,
    channel: str
) -> bool
```

**Purpose**: Add a user to a community  
**Returns**: True if added successfully  
**Raises**: `ValueError` if community_id invalid or parameters missing  
**Invariants**:
- `community_id` must reference existing group
- `user_id` required (phone, chat_id, etc.)
- `channel` in ["telegram", "sms", "ussd", "whatsapp"]
- UNIQUE(community_id, user_id, channel) enforced at DB level

---

#### `remove_member_from_community`
```python
def remove_member_from_community(
    community_id: str,
    user_id: str,
    channel: str
) -> bool
```

**Purpose**: Remove a user from a community (soft delete)  
**Returns**: True if removed successfully  
**Invariants**:
- Sets `active=0` (soft delete)
- Does not physically delete record

---

#### `get_community_members`
```python
def get_community_members(
    community_id: str,
    channel: Optional[str] = None
) -> List[str]
```

**Purpose**: Resolve members of a community  
**Returns**: List of user IDs  
**Raises**: `ValueError` if community_id is None or invalid  
**Invariants**:
- **MANDATORY**: `community_id` required (enforces WHERE community_id = ?)
- Only returns `active=1` members
- If `channel` provided, filters by channel
- **SECURITY**: This is the ONLY method that resolves recipients

---

### Message Delivery (SECURITY-CRITICAL)

#### `deliver_announcement`
```python
async def deliver_announcement(
    announcement_id: str,
    admin_id: str
) -> dict
```

**Purpose**: Deliver an announcement to community members  
**Returns**: Delivery result dict with keys: `delivered`, `failed`, `community_id`, `recipients`  
**Raises**: `ValueError` if announcement invalid or admin not authorized  
**Invariants**:
- **SECURITY**: Enforces admin→community binding
- Admin must match `community.admin_id`
- Recipients resolved via `get_community_members()` (kernel-level scoping)
- Emits `COMMUNITY_MESSAGE_DELIVER` event with pre-scoped recipients
- **FAIL-CLOSED**: Rejects on any validation failure (no partial send)

---

### Inquiry Handling

#### `handle_inquiry`
```python
async def handle_inquiry(
    group_id: str,
    question: str,
    source: str
) -> Tuple[str, bool]
```

**Purpose**: Handle an inquiry (with cache hit/miss logic)  
**Returns**: Tuple of (answer, is_cache_hit)  
**Invariants**:
- Normalizes question (lowercase, strip whitespace)
- Checks cache first
- Increments `hit_count` on cache hit
- Returns ("No cached answer", False) on miss

---

#### `reply_to_inquiry`
```python
async def reply_to_inquiry(
    inquiry_id: str,
    answer: str
) -> bool
```

**Purpose**: Reply to a pending inquiry  
**Returns**: True if successful  
**Invariants**:
- Updates inquiry record with answer
- Emits `COMMUNITY_INQUIRY_REPLIED` event

---

#### `add_cached_inquiry`
```python
async def add_cached_inquiry(
    group_id: str,
    question: str,
    answer: str
) -> CommunityInquiryDTO
```

**Purpose**: Add a pre-answered inquiry to cache  
**Returns**: Newly created inquiry DTO  
**Invariants**:
- Normalizes question before storing
- Sets `hit_count=0` initially

---

## Data Transfer Objects (DTOs)

### CommunityGroupDTO
```python
@dataclass
class CommunityGroupDTO:
    id: str
    name: str
    description: str
    group_type: str
    tags: str  # JSON array
    location: str
    admin_id: str
    trust_level: str
    preferred_channels: str
    active: bool
    created_at: Optional[datetime] = None
```

### CommunityEventDTO
```python
@dataclass
class CommunityEventDTO:
    id: str
    group_id: str
    title: str
    event_type: str
    start_time: datetime
    end_time: Optional[datetime]
    recurrence: Optional[str]
    visibility: str
    language: str
    created_at: Optional[datetime] = None
```

### CommunityAnnouncementDTO
```python
@dataclass
class CommunityAnnouncementDTO:
    id: str
    group_id: str
    message: str
    urgency: str
    expires_at: Optional[datetime]
    target_audience: str
    created_at: Optional[datetime] = None
```

### CommunityInquiryDTO
```python
@dataclass
class CommunityInquiryDTO:
    id: str
    group_id: str
    normalized_question: str
    answer: str
    hit_count: int
    last_updated: Optional[datetime] = None
```

---

## Security Invariants (NON-NEGOTIABLE)

### Invariant 1: Mandatory Community Scoping
- Every message MUST have a valid `community_id`
- Messages without `community_id` MUST be rejected before delivery
- Enforced at kernel level, not adapters

### Invariant 2: Admin → Community Binding
- Admin identity bound to exactly one community per session
- Admin cannot send messages outside their bound community
- Enforced in `deliver_announcement()`

### Invariant 3: Recipient Resolution Firewall
- Message fan-out MUST resolve recipients only via `WHERE community_id = ?`
- NO global member list used for delivery
- Enforced in `get_community_members()`

### Invariant 4: Fail Closed
- If community validation fails: NO partial send, NO fallback, NO default, NO silent ignore
- Explicit `ValueError` raised
- Enforced across all methods

### Invariant 5: Adapter Ignorance
- USSD/SMS/Bot adapters MUST NOT decide recipients
- MUST NOT override `community_id`
- MUST NOT format delivery lists
- All routing decisions live in the kernel

---

## Events Emitted

| Event Name | Payload | Purpose |
|------------|---------|---------|
| `COMMUNITY_GROUP_REGISTERED` | `{id, name, location, tags}` | Group created |
| `COMMUNITY_EVENT_CREATED` | `{id, group_id, title, start_time}` | Event published |
| `COMMUNITY_ANNOUNCEMENT_CREATED` | `{id, group_id, message, urgency}` | Announcement created |
| `COMMUNITY_MESSAGE_DELIVER` | `{announcement_id, community_id, message, recipients, urgency}` | Delivery request (pre-scoped) |
| `COMMUNITY_INQUIRY_REPLIED` | `{inquiry_id, answer}` | Inquiry answered |

---

## Usage Patterns

### Pattern 1: Register and Discover Groups
```python
# Register
group = await community.register_group(
    name="St. Mary's Church",
    tags=["church", "catholic"],
    location="Nairobi",
    admin_id="admin-123"
)

# Discover
churches = community.discover_groups(
    location="Nairobi",
    tag_filter=["church"]
)
```

### Pattern 2: Publish and Deliver Announcements
```python
# Publish
announcement = await community.publish_announcement(
    group_id="GRP-ABC123",
    message="Sunday service at 9 AM",
    urgency="normal"
)

# Add members
community.add_member_to_community("GRP-ABC123", "254712345678", "sms")
community.add_member_to_community("GRP-ABC123", "123456789", "telegram")

# Deliver (with admin binding check)
result = await community.deliver_announcement(
    announcement_id=announcement.id,
    admin_id="admin-123"
)
# result = {"delivered": 2, "failed": 0, "community_id": "GRP-ABC123", "recipients": [...]}
```

### Pattern 3: Handle Inquiries with Cache
```python
# Handle inquiry (cache hit/miss)
answer, is_hit = await community.handle_inquiry(
    group_id="GRP-ABC123",
    question="What time is Sunday service?",
    source="254712345678"
)

# Add to cache
await community.add_cached_inquiry(
    group_id="GRP-ABC123",
    question="What time is Sunday service?",
    answer="Sunday service is at 9 AM"
)
```

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

**Non-breaking changes**:
- Adding new optional parameters (with defaults)
- Adding new methods
- Adding new DTOs
- Adding new events

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-28 | Initial locked specification |

---

**Signed**: FAANG Staff Engineer  
**Approved for**: Production Deployment
