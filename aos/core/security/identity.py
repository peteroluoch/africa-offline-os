from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from aos.core.config import settings


class NodeIdentityManager:
    """
    Manages the cryptographic identity of an A-OS Node.
    Uses Ed25519 for high-performance, compact signatures.
    """

    SEED_FILE = "node_id.seed"
    PUB_FILE = "node_id.pub"

    def __init__(self, keys_dir: str | Path | None = None):
        self.keys_dir = Path(keys_dir or settings.keys_dir)
        self._private_key: ed25519.Ed25519PrivateKey | None = None
        self._public_key: ed25519.Ed25519PublicKey | None = None

    def ensure_identity(self) -> None:
        """Ensure node keys exist. Loads if present, generates if missing."""
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        seed_path = self.keys_dir / self.SEED_FILE

        if seed_path.exists():
            self._load_keys()
        else:
            self._generate_keys()

    def _generate_keys(self) -> None:
        """Generate new Ed25519 keys and save to disk."""
        private_key = ed25519.Ed25519PrivateKey.generate()

        # Save private seed (unencrypted for kernel-level auto-boot)
        # In a real "GENIUS" level scenario, we might use HW-backed storage.
        seed_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        (self.keys_dir / self.SEED_FILE).write_bytes(seed_bytes)

        # Save public key
        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        (self.keys_dir / self.PUB_FILE).write_bytes(pub_bytes)

        self._private_key = private_key
        self._public_key = public_key

    def _load_keys(self) -> None:
        """Load keys from disk."""
        seed_bytes = (self.keys_dir / self.SEED_FILE).read_bytes()
        self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)
        self._public_key = self._private_key.public_key()

    def get_public_key(self) -> bytes:
        """Return the public key in raw bytes."""
        if not self._public_key:
            self._load_keys()
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def sign(self, data: bytes) -> bytes:
        """Sign data using the node's private key."""
        if not self._private_key:
            self._load_keys()
        return self._private_key.sign(data)

    def verify(self, data: bytes, signature: bytes, public_key_bytes: bytes) -> bool:
        """Verify a signature against data and a public key."""
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            pub_key.verify(signature, data)
            return True
        except Exception:
            return False
