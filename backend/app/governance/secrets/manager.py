import os
from typing import Dict, Optional, Protocol


class SecretProvider(Protocol):
    def get(self, key: str) -> Optional[str]: ...
    def set(self, key: str, value: str) -> None: ...


class MemorySecretProvider:
    """In-memory secret store."""
    _store: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value


class EnvironmentProvider:
    """Reads secrets from environment variables."""
    def get(self, key: str) -> Optional[str]:
        return os.environ.get(key)

    def set(self, key: str, value: str) -> None:
        os.environ[key] = value


class SecretManager:
    """Multi-provider secret manager with fallback chain."""

    def __init__(self):
        self.memory = MemorySecretProvider()
        self.env = EnvironmentProvider()

    def get_secret(self, key: str) -> Optional[str]:
        """Try memory first, then environment."""
        return self.memory.get(key) or self.env.get(key)

    def set_secret(self, key: str, value: str):
        """Store in memory provider."""
        self.memory.set(key, value)
