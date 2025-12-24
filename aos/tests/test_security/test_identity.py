import pytest
import shutil
from pathlib import Path
from aos.core.security.identity import NodeIdentityManager
from aos.core.config import settings

@pytest.fixture
def temp_keys_dir(tmp_path):
    """Fixture to provide a temporary directory for keys."""
    keys_path = tmp_path / "keys"
    # Monkeypatch settings to use temp keys dir
    original_keys_dir = settings.keys_dir
    settings.keys_dir = str(keys_path)
    yield keys_path
    settings.keys_dir = original_keys_dir

def test_generate_and_load_keys(temp_keys_dir):
    """Verify that keys are generated and can be reloaded."""
    manager = NodeIdentityManager()
    
    # First time: generate
    manager.ensure_identity()
    
    private_key_path = temp_keys_dir / "node_id.seed"
    public_key_path = temp_keys_dir / "node_id.pub"
    
    assert private_key_path.exists()
    assert public_key_path.exists()
    
    pub_key_original = public_key_path.read_bytes()
    
    # Second time: reload
    manager_reload = NodeIdentityManager()
    manager_reload.ensure_identity()
    
    pub_key_reloaded = public_key_path.read_bytes()
    assert pub_key_original == pub_key_reloaded

def test_sign_and_verify(temp_keys_dir):
    """Verify that we can sign data and verify the signature."""
    manager = NodeIdentityManager()
    manager.ensure_identity()
    
    data = b"Africa Offline OS - Integrity Check"
    signature = manager.sign(data)
    
    assert len(signature) == 64  # Ed25519 signature length
    
    is_valid = manager.verify(data, signature, manager.get_public_key())
    assert is_valid is True

def test_verify_failure(temp_keys_dir):
    """Verify that invalid signatures or modified data fail verification."""
    manager = NodeIdentityManager()
    manager.ensure_identity()
    
    data = b"Original Data"
    signature = manager.sign(data)
    
    # Verify with modified data
    assert manager.verify(b"Modified Data", signature, manager.get_public_key()) is False
    
    # Verify with random signature
    assert manager.verify(data, b"0" * 64, manager.get_public_key()) is False
