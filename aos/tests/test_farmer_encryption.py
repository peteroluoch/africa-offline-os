import pytest
import sqlite3
import os
from aos.core.security.encryption import SymmetricEncryption
from aos.db.repository import FarmerRepository
from aos.db.models import FarmerDTO
from datetime import datetime

def test_farmer_encryption_at_rest():
    # 1. Setup
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE farmers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            contact TEXT,
            metadata TEXT,
            created_at TIMESTAMP
        )
    """)
    
    # Derive a key
    salt = os.urandom(16)
    key = SymmetricEncryption.derive_key(salt, "test-secret")
    encryptor = SymmetricEncryption(key)
    
    repo = FarmerRepository(conn, encryptor)
    
    # 2. Save a farmer
    farmer = FarmerDTO(
        id="farmer_001",
        name="James Mwangi",
        location="Nyeri, Kenya",
        contact="+254712345678",
        metadata={"crop": "Coffee"},
        created_at=datetime.utcnow()
    )
    repo.save(farmer)
    
    # 3. Verify raw DB content is encrypted
    cursor = conn.execute("SELECT location, contact FROM farmers WHERE id = 'farmer_001'")
    row = cursor.fetchone()
    
    # Location and contact should be bytes (nonce + ciphertext) and not plaintext
    assert isinstance(row["location"], bytes)
    assert b"Nyeri" not in row["location"]
    assert b"+254" not in row["contact"]
    
    # 4. Verify Repository decrypts correctly
    loaded = repo.get_by_id("farmer_001")
    assert loaded.location == "Nyeri, Kenya"
    assert loaded.contact == "+254712345678"
    assert loaded.name == "James Mwangi" # Name stays plaintext for indexing/display (by choice)
