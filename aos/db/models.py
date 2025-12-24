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
    sub: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConfigDTO(BaseModel):
    """Data Transfer Object for node configuration."""
    key: str
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
