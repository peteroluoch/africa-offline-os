import pytest
import os
from aos.core.security.encryption import SymmetricEncryption

def test_encryption_decryption_cycle():
    """Verify that data can be encrypted and decrypted correctly."""
    key = os.urandom(32)
    cipher = SymmetricEncryption(key)
    
    original_data = b"Secret Offline Data"
    encrypted = cipher.encrypt(original_data)
    
    assert encrypted != original_data
    assert len(encrypted) > len(original_data) # Includes nonce and tag
    
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == original_data

def test_invalid_key_length():
    """Verify that invalid key lengths are rejected."""
    with pytest.raises(ValueError, match="Key must be 32 bytes"):
        SymmetricEncryption(b"short_key")

def test_integrity_failure():
    """Verify that tempered data fails decryption."""
    key = os.urandom(32)
    cipher = SymmetricEncryption(key)
    
    encrypted = cipher.encrypt(b"Original")
    
    # Tamper with the ciphertext
    tampered = bytearray(encrypted)
    tampered[-1] ^= 0xFF 
    
    with pytest.raises(ValueError, match="Decryption failed"):
        cipher.decrypt(bytes(tampered))

def test_different_nonces():
    """Verify that same data results in different ciphertexts (due to random nonces)."""
    key = os.urandom(32)
    cipher = SymmetricEncryption(key)
    
    data = b"Sensitive Info"
    enc1 = cipher.encrypt(data)
    enc2 = cipher.encrypt(data)
    
    assert enc1 != enc2
