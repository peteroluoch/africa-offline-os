from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NodeDTO(BaseModel):
    """Data Transfer Object representing an A-OS Node."""
    id: str
    public_key: bytes
    alias: str | None = None
    status: str = "active"
    last_seen: datetime = Field(default_factory=datetime.utcnow)

class OperatorDTO(BaseModel):
    """Data Transfer Object representing a local operator."""
    id: str
    username: str
    role_id: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

class RoleDTO(BaseModel):
    """Data Transfer Object representing a role."""
    id: str
    name: str
    permissions: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConfigDTO(BaseModel):
    """Data Transfer Object for node configuration."""
    key: str
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FarmerDTO(BaseModel):
    """Represents a farmer registered in the mesh."""
    id: str
    name: str
    location: str
    contact: str
    metadata: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CropDTO(BaseModel):
    """Represents a crop type."""
    id: str
    name: str
    crop_type: str
    growing_season: str

class HarvestDTO(BaseModel):
    """Represents a harvest record."""
    id: str
    farmer_id: str
    crop_id: str
    quantity: float
    unit: str = "kg"
    quality_grade: str
    harvest_date: datetime
    status: str = "stored"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommunityGroupDTO(BaseModel):
    """Represents a trusted local group."""
    id: str
    name: str
    description: str | None = None
    group_type: str | None = None
    tags: str = "[]" # JSON list of free-text tags
    location: str | None = None
    admin_id: str | None = None
    trust_level: str = "local"
    preferred_channels: str = "ussd,sms"
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommunityEventDTO(BaseModel):
    """Represents a scheduled community event."""
    id: str
    group_id: str
    title: str
    event_type: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    recurrence: str | None = None
    visibility: str = "public"
    language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommunityAnnouncementDTO(BaseModel):
    """Represents a one-way announcement."""
    id: str
    group_id: str
    message: str
    urgency: str = "normal"
    expires_at: datetime | None = None
    target_audience: str = "public"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommunityInquiryDTO(BaseModel):
    """Represents a cached inquiry response."""
    id: str
    group_id: str
    normalized_question: str
    answer: str
    hit_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class TransportZoneDTO(BaseModel):
    """Represents a road, area, stage, or junction."""
    id: str
    name: str
    type: str # road, area, stage, junction
    location_scope: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrafficSignalDTO(BaseModel):
    """Represents a traffic signal (state of a zone)."""
    id: str
    zone_id: str
    state: str # flowing, slow, blocked
    source: str # user, agent, authority
    confidence_score: float = 1.0
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

class TransportAvailabilityDTO(BaseModel):
    """Represents vehicle availability to a destination."""
    id: str
    zone_id: str
    destination: str
    availability_state: str # available, limited, none
    reported_by: str
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
