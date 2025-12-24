import pytest
import sqlite3
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS
from aos.core.security.password import verify_password, get_password_hash

@pytest.fixture
def db():
    # Use in-memory DB for speed and isolation
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

def test_iam_bootstrap(db):
    """Verify migrations create admin user correctly."""
    mgr = MigrationManager(db)
    
    # Apply all migrations
    mgr.apply_migrations(MIGRATIONS)
    
    # 1. Verify Roles
    cursor = db.execute("SELECT name, permissions FROM roles WHERE name='admin'")
    role = cursor.fetchone()
    assert role is not None
    assert role[0] == "admin"
    assert '"*"' in role[1] # Check for wildcard permission
    
    # 2. Verify Admin Operator
    cursor = db.execute("SELECT username, password_hash FROM operators WHERE username='admin'")
    op = cursor.fetchone()
    assert op is not None
    username, pw_hash = op
    
    # 3. Verify Password Integrity
    # We try to verify the default password 'aos_root_2025' against the stored hash
    assert verify_password("aos_root_2025", pw_hash)
    assert not verify_password("wrong_password", pw_hash)

def test_create_new_operator(db):
    """Verify we can create a new operator with hashed password."""
    mgr = MigrationManager(db)
    mgr.apply_migrations(MIGRATIONS)
    
    # Helper to get role_id
    role_id = db.execute("SELECT id FROM roles WHERE name='admin'").fetchone()[0]
    
    # Create new user
    new_hash = get_password_hash("new_secret")
    db.execute(
        "INSERT INTO operators (id, username, password_hash, role_id, created_at) VALUES (?, ?, ?, ?, ?)",
        ("new-id", "new_user", new_hash, role_id, "2025-01-01T00:00:00")
    )
    
    # Verify login
    cursor = db.execute("SELECT password_hash FROM operators WHERE username='new_user'")
    stored_hash = cursor.fetchone()[0]
    
    assert verify_password("new_secret", stored_hash)
