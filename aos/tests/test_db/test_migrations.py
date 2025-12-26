
import pytest

from aos.db.engine import connect
from aos.db.migrations import MigrationManager


@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = connect(str(db_path))
    yield conn, db_path
    conn.close()

def test_migration_manager_initialization(temp_db):
    """Verify that MigrationManager creates the migrations table."""
    conn, _ = temp_db
    manager = MigrationManager(conn)
    manager.ensure_migration_table()

    # Check if table exists
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
    assert cursor.fetchone() is not None

def test_apply_migrations(temp_db):
    """Verify that multiple migrations can be applied in order."""
    conn, _ = temp_db
    manager = MigrationManager(conn)
    manager.ensure_migration_table()

    migrations = [
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);",
        "ALTER TABLE test_table ADD COLUMN description TEXT;"
    ]

    manager.apply_migrations(migrations)

    # Check schema
    cursor = conn.execute("PRAGMA table_info(test_table)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "id" in columns
    assert "name" in columns
    assert "description" in columns

    # Check version tracking
    cursor = conn.execute("SELECT COUNT(*) FROM schema_migrations")
    assert cursor.fetchone()[0] == 2

def test_migration_idempotency(temp_db):
    """Verify that migrations are not applied twice."""
    conn, _ = temp_db
    manager = MigrationManager(conn)
    manager.ensure_migration_table()

    migrations = [
        "CREATE TABLE t1 (id int);"
    ]

    manager.apply_migrations(migrations)

    # Run again - should not fail or add new records if versioning is checked
    # (Implementation detail: manager should hash or index migrations)
    # Simple strategy: migrations list index + hashed content
    manager.apply_migrations(migrations)

    cursor = conn.execute("SELECT COUNT(*) FROM schema_migrations")
    assert cursor.fetchone()[0] == 1
