from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class SymmetricEncryption:
    """
    High-performance AEAD encryption using ChaCha20-Poly1305.
    Ideal for mobile/edge devices due to software-friendly design.
    """

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes (256 bits).")
        self.aead = ChaCha20Poly1305(key)

    @staticmethod
    def derive_key(salt: bytes, secret: str, iterations: int = 100000) -> bytes:
        """
        Derive a 32-byte key from a secret and salt using PBKDF2-HMAC-SHA256.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(secret.encode())

    def encrypt(self, data: bytes, associated_data: bytes | None = None) -> bytes:
        """
        Encrypt data and return ciphertext prefixed with the nonce.
        Format: [12 bytes nonce][ciphertext + 16 bytes tag]
        """
        nonce = os.urandom(12)
        ciphertext = self.aead.encrypt(nonce, data, associated_data)
        return nonce + ciphertext

    def decrypt(self, nonce_prefixed_ciphertext: bytes, associated_data: bytes | None = None) -> bytes:
        """
        Decrypt nonce-prefixed ciphertext.
        """
        if len(nonce_prefixed_ciphertext) < 12:
            raise ValueError("Invalid ciphertext: too short.")

        nonce = nonce_prefixed_ciphertext[:12]
        ciphertext = nonce_prefixed_ciphertext[12:]

        try:
            return self.aead.decrypt(nonce, ciphertext, associated_data)
        except Exception:
            raise ValueError("Decryption failed (integrity check failed).")
