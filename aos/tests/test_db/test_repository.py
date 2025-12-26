
import pytest

from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS
from aos.db.models import NodeDTO, OperatorDTO
from aos.db.repository import NodeRepository, OperatorRepository


@pytest.fixture
def db_conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = connect(str(db_path))

    # Run migrations
    manager = MigrationManager(conn)
    manager.apply_migrations(MIGRATIONS)

    yield conn
    conn.close()

def test_node_repository_upsert(db_conn):
    repo = NodeRepository(db_conn)
    node = NodeDTO(id="n1", public_key=b"pk1", alias="Node 1")

    repo.upsert(node)

    fetched = repo.get_by_id("n1")
    assert fetched is not None
    assert fetched.alias == "Node 1"
    assert fetched.public_key == b"pk1"

def test_operator_repository_save(db_conn):
    repo = OperatorRepository(db_conn)
    op = OperatorDTO(id="op1", sub="sub-123", role="admin")

    repo.save(op)

    fetched = repo.get_by_id("op1")
    assert fetched is not None
    assert fetched.sub == "sub-123"
    assert fetched.role == "admin"

def test_list_all_records(db_conn):
    repo = NodeRepository(db_conn)
    repo.upsert(NodeDTO(id="n1", public_key=b"p1"))
    repo.upsert(NodeDTO(id="n2", public_key=b"p2"))

    all_nodes = repo.list_all()
    assert len(all_nodes) == 2
    ids = [n.id for n in all_nodes]
    assert "n1" in ids
    assert "n2" in ids
