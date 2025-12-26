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
    hashed_password: str
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
