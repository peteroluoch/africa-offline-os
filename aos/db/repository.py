from __future__ import annotations
import sqlite3
from typing import TypeVar, Generic, List, Type, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseRepository(Generic[T]):
    """
    Base Repository using Pydantic DTOs for type safety.
    """
    
    def __init__(self, connection: sqlite3.Connection, model_class: Type[T], table_name: str):
        self.conn = connection
        self.model_class = model_class
        self.table_name = table_name

    def _row_to_model(self, row: sqlite3.Row) -> T:
        return self.model_class.model_validate(dict(row))

    def get_by_id(self, id: Any) -> T | None:
        """Fetch a single record by its primary key."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_model(row) if row else None

    def list_all(self) -> List[T]:
        """Fetch all records from the table."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(f"SELECT * FROM {self.table_name}")
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def delete(self, id: Any) -> bool:
        """Delete a record by its primary key."""
        cursor = self.conn.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
        self.conn.commit()
        return cursor.rowcount > 0

from aos.db.models import NodeDTO, OperatorDTO

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
            INSERT OR REPLACE INTO operators (id, sub, role, created_at)
            VALUES (?, ?, ?, ?)
        """, (operator.id, operator.sub, operator.role, operator.created_at))
        self.conn.commit()
