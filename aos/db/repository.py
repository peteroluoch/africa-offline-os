from __future__ import annotations

import json
import sqlite3
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from aos.core.security.encryption import SymmetricEncryption
from aos.core.config import settings

T = TypeVar("T", bound=BaseModel)

class SecureRepositoryMixin:
    """
    Mixin to provide transparent encryption/decryption for specific fields.
    """
    def __init__(self, master_encryption: SymmetricEncryption, encrypted_fields: list[str]):
        self.encryptor = master_encryption
        self.encrypted_fields = encrypted_fields

    def _encrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Encrypt configured fields in the dictionary."""
        for field in self.encrypted_fields:
            if field in data and data[field]:
                val = data[field]
                if not isinstance(val, bytes):
                    val = str(val).encode()
                data[field] = self.encryptor.encrypt(val)
        return data

    def _decrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Decrypt configured fields in the dictionary."""
        for field in self.encrypted_fields:
            if field in data and data[field]:
                try:
                    decrypted = self.encryptor.decrypt(data[field])
                    data[field] = decrypted.decode()
                except Exception as e:
                    print(f"[Security] Decryption warning for {field}: {e}")
        return data

class BaseRepository(Generic[T]):
    """
    Base Repository using Pydantic DTOs for type safety.
    """

    def __init__(self, connection: sqlite3.Connection, model_class: type[T], table_name: str):
        self.conn = connection
        self.model_class = model_class
        self.table_name = table_name

    def _row_to_model(self, row: sqlite3.Row) -> T:
        data = dict(row)
        data = self._preprocess_data(data)
        return self.model_class.model_validate(data)

    def _preprocess_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Hook to preprocess database row dict before Pydantic validation."""
        return data

    def get_by_id(self, id: Any) -> T | None:
        """Fetch a single record by its primary key."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def list_all(self) -> list[T]:
        """Fetch all records from the table."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(f"SELECT * FROM {self.table_name}")
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def delete(self, id: Any) -> bool:
        """Delete a record by its primary key."""
        cursor = self.conn.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
        self.conn.commit()
        return cursor.rowcount > 0

from aos.db.models import (
    OperatorDTO, NodeDTO, FarmerDTO, HarvestDTO, CropDTO,
    CommunityGroupDTO, CommunityEventDTO, CommunityAnnouncementDTO, CommunityInquiryDTO,
    TransportZoneDTO, TrafficSignalDTO, TransportAvailabilityDTO
)


class NodeRepository(BaseRepository[NodeDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, NodeDTO, "nodes")

    def upsert(self, node: NodeDTO) -> None:
        """Insert or update a node record."""
        self.conn.execute("""
            INSERT INTO nodes (id, public_key, alias, status, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                public_key=excluded.public_key,
                alias=excluded.alias,
                status=excluded.status,
                last_seen=excluded.last_seen
        """, (node.id, node.public_key, node.alias, node.status, node.last_seen))
        self.conn.commit()

class OperatorRepository(BaseRepository[OperatorDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, OperatorDTO, "operators")

    def save(self, operator: OperatorDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO operators (id, username, password_hash, role_id, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (operator.id, operator.username, operator.password_hash, operator.role_id, operator.created_at, operator.last_login))
        self.conn.commit()

class FarmerRepository(BaseRepository[FarmerDTO], SecureRepositoryMixin):
    def __init__(self, connection: sqlite3.Connection, encryptor: SymmetricEncryption):
        BaseRepository.__init__(self, connection, FarmerDTO, "farmers")
        SecureRepositoryMixin.__init__(self, encryptor, ["location", "contact"])

    def _row_to_model(self, row: sqlite3.Row) -> FarmerDTO:
        data = dict(row)
        data = self._decrypt_dict(data)
        data = self._preprocess_data(data)
        return self.model_class.model_validate(data)

    def _preprocess_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("metadata") and isinstance(data["metadata"], str):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except json.JSONDecodeError:
                data["metadata"] = {}
        return data

    def save(self, farmer: FarmerDTO) -> None:
        data = farmer.model_dump()
        data = self._encrypt_dict(data)
        
        self.conn.execute("""
            INSERT OR REPLACE INTO farmers (id, name, location, contact, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["id"],
            data["name"],
            data["location"],
            data["contact"],
            json.dumps(data["metadata"]),
            data["created_at"]
        ))
        self.conn.commit()

class CropRepository(BaseRepository[CropDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, CropDTO, "crops")

class HarvestRepository(BaseRepository[HarvestDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, HarvestDTO, "harvests")

    def save(self, harvest: HarvestDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO harvests (id, farmer_id, crop_id, quantity, unit, quality_grade, harvest_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            harvest.id,
            harvest.farmer_id,
            harvest.crop_id,
            harvest.quantity,
            harvest.unit,
            harvest.quality_grade,
            harvest.harvest_date,
            harvest.status,
            harvest.created_at
        ))
        self.conn.commit()

class CommunityGroupRepository(BaseRepository[CommunityGroupDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, CommunityGroupDTO, "community_groups")

    def save(self, group: CommunityGroupDTO) -> None:
        import logging
        logger = logging.getLogger("aos.db.repository")
        
        # Check if group exists
        cursor = self.conn.execute("SELECT id FROM community_groups WHERE id = ?", (group.id,))
        exists = cursor.fetchone() is not None
        
        logger.info(f"Saving group {group.id}: exists={exists}, code={group.community_code}, active={group.code_active}")
        
        if exists:
            # Update existing group
            logger.info(f"Updating existing group {group.id}")
            self.conn.execute("""
                UPDATE community_groups 
                SET name = ?, description = ?, group_type = ?, tags = ?, location = ?, 
                    admin_id = ?, trust_level = ?, preferred_channels = ?, invite_slug = ?, 
                    community_code = ?, code_active = ?, active = ?
                WHERE id = ?
            """, (group.name, group.description, group.group_type, group.tags, group.location, 
                  group.admin_id, group.trust_level, group.preferred_channels, group.invite_slug, 
                  group.community_code, group.code_active, group.active, group.id))
        else:
            # Insert new group
            logger.info(f"Inserting new group {group.id}")
            self.conn.execute("""
                INSERT INTO community_groups (id, name, description, group_type, tags, location, admin_id, trust_level, preferred_channels, invite_slug, community_code, code_active, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (group.id, group.name, group.description, group.group_type, group.tags, group.location, group.admin_id, group.trust_level, group.preferred_channels, group.invite_slug, group.community_code, group.code_active, group.active, group.created_at))
        
        self.conn.commit()
        logger.info(f"Successfully saved group {group.id}")

    def get_by_slug(self, slug: str) -> CommunityGroupDTO | None:
        """Fetch a single record by its invite slug."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(f"SELECT * FROM {self.table_name} WHERE invite_slug = ?", (slug,))
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def get_by_code(self, code: str) -> CommunityGroupDTO | None:
        """Fetch a single active community by its code."""
        import logging
        logger = logging.getLogger(__name__)
        
        self.conn.row_factory = sqlite3.Row
        # Case-insensitive lookup using UPPER
        logger.info(f"[DB Query] Looking for code: '{code}' (stripped: '{code.strip()}')")
        
        cursor = self.conn.execute(
            f"SELECT * FROM {self.table_name} WHERE UPPER(community_code) = UPPER(?) AND code_active = 1",
            (code.strip(),)
        )
        row = cursor.fetchone()
        
        if row:
            logger.info(f"[DB Query] FOUND: {dict(row)}")
        else:
            # Debug: Check if code exists but is inactive
            cursor2 = self.conn.execute(
                f"SELECT id, name, community_code, code_active FROM {self.table_name} WHERE UPPER(community_code) = UPPER(?)",
                (code.strip(),)
            )
            inactive_row = cursor2.fetchone()
            if inactive_row:
                logger.warning(f"[DB Query] Code exists but code_active={inactive_row['code_active']}: {dict(inactive_row)}")
            else:
                logger.warning(f"[DB Query] Code '{code}' not found in database at all")
        
        return self._row_to_model(row) if row else None

class CommunityEventRepository(BaseRepository[CommunityEventDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, CommunityEventDTO, "community_events")

    def save(self, event: CommunityEventDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO community_events (id, group_id, title, event_type, start_time, end_time, recurrence, visibility, language, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event.id, event.group_id, event.title, event.event_type, event.start_time, event.end_time, event.recurrence, event.visibility, event.language, event.created_at))
        self.conn.commit()

class CommunityAnnouncementRepository(BaseRepository[CommunityAnnouncementDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, CommunityAnnouncementDTO, "community_announcements")

    def save(self, announcement: CommunityAnnouncementDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO community_announcements (id, group_id, message, urgency, expires_at, target_audience, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (announcement.id, announcement.group_id, announcement.message, announcement.urgency, announcement.expires_at, announcement.target_audience, announcement.created_at))
        self.conn.commit()

class CommunityInquiryRepository(BaseRepository[CommunityInquiryDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, CommunityInquiryDTO, "community_inquiry_cache")

    def save(self, inquiry: CommunityInquiryDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO community_inquiry_cache (id, group_id, normalized_question, answer, hit_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (inquiry.id, inquiry.group_id, inquiry.normalized_question, inquiry.answer, inquiry.hit_count, inquiry.last_updated))
        self.conn.commit()

class TransportZoneRepository(BaseRepository[TransportZoneDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, TransportZoneDTO, "transport_zones")

    def save(self, zone: TransportZoneDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO transport_zones (id, name, type, location_scope, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (zone.id, zone.name, zone.type, zone.location_scope, zone.active, zone.created_at))
        self.conn.commit()

class TrafficSignalRepository(BaseRepository[TrafficSignalDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, TrafficSignalDTO, "traffic_signals")

    def save(self, signal: TrafficSignalDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO traffic_signals (id, zone_id, state, source, confidence_score, reported_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (signal.id, signal.zone_id, signal.state, signal.source, signal.confidence_score, signal.reported_at, signal.expires_at))
        self.conn.commit()

class TransportAvailabilityRepository(BaseRepository[TransportAvailabilityDTO]):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection, TransportAvailabilityDTO, "transport_availability")

    def save(self, availability: TransportAvailabilityDTO) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO transport_availability (id, zone_id, destination, availability_state, reported_by, reported_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (availability.id, availability.zone_id, availability.destination, availability.availability_state, availability.reported_by, availability.reported_at, availability.expires_at))
        self.conn.commit()
