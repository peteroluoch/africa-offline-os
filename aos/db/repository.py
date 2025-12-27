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

from aos.db.models import CropDTO, FarmerDTO, HarvestDTO, NodeDTO, OperatorDTO


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
        """, (operator.id, operator.username, operator.hashed_password, operator.role_id, operator.created_at, operator.last_login))
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
