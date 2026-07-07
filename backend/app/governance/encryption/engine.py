import base64
import hashlib
import os
import uuid
from typing import Dict, Optional
from app.governance.models import KeyMetadata


class EncryptionEngine:
    """
    Encryption engine with key rotation.
    Uses Fernet (from cryptography lib) if available, otherwise falls back
    to a simple XOR cipher for MVP/testing purposes.
    """

    _keys: Dict[str, bytes] = {}
    _key_metadata: Dict[str, KeyMetadata] = {}
    _active_key_id: Optional[str] = None

    @classmethod
    def generate_key(cls, algorithm: str = "fernet") -> str:
        """Generate and register a new encryption key."""
        key_id = str(uuid.uuid4())

        try:
            from cryptography.fernet import Fernet
            raw_key = Fernet.generate_key()
        except ImportError:
            # Fallback: 32-byte random key for XOR
            raw_key = os.urandom(32)

        cls._keys[key_id] = raw_key
        cls._key_metadata[key_id] = KeyMetadata(
            key_id=key_id,
            algorithm=algorithm,
            version=len(cls._key_metadata) + 1,
        )
        cls._active_key_id = key_id
        return key_id

    @classmethod
    def encrypt(cls, plaintext: str, key_id: str = None) -> str:
        """Encrypt plaintext with the specified (or active) key."""
        kid = key_id or cls._active_key_id
        if not kid or kid not in cls._keys:
            raise ValueError("No encryption key available")

        raw_key = cls._keys[kid]

        try:
            from cryptography.fernet import Fernet
            f = Fernet(raw_key)
            return f.encrypt(plaintext.encode()).decode()
        except ImportError:
            # XOR fallback
            data = plaintext.encode()
            encrypted = bytes(b ^ raw_key[i % len(raw_key)] for i, b in enumerate(data))
            return base64.b64encode(encrypted).decode()

    @classmethod
    def decrypt(cls, ciphertext: str, key_id: str = None) -> str:
        """Decrypt ciphertext with the specified (or active) key."""
        kid = key_id or cls._active_key_id
        if not kid or kid not in cls._keys:
            raise ValueError("No encryption key available")

        raw_key = cls._keys[kid]

        try:
            from cryptography.fernet import Fernet
            f = Fernet(raw_key)
            return f.decrypt(ciphertext.encode()).decode()
        except ImportError:
            # XOR fallback
            encrypted = base64.b64decode(ciphertext.encode())
            decrypted = bytes(b ^ raw_key[i % len(raw_key)] for i, b in enumerate(encrypted))
            return decrypted.decode()

    @classmethod
    def rotate_key(cls) -> str:
        """Generate a new key and make it active. Old keys remain for decryption."""
        return cls.generate_key()

    @classmethod
    def get_active_key_id(cls) -> Optional[str]:
        return cls._active_key_id
