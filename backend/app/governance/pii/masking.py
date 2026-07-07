import hashlib
import uuid
from typing import Protocol


class MaskingStrategy(Protocol):
    def mask(self, value: str) -> str: ...


class PartialMask:
    """Keeps first and last character, masks the rest."""
    def mask(self, value: str) -> str:
        if len(value) <= 2:
            return "*" * len(value)
        return value[0] + "*" * (len(value) - 2) + value[-1]


class FullMask:
    """Replaces entire value with asterisks."""
    def mask(self, value: str) -> str:
        return "*" * len(value)


class HashMask:
    """Replaces value with its SHA-256 hash."""
    def mask(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()


class TokenizeMask:
    """Replaces value with a random token."""
    def mask(self, value: str) -> str:
        return f"TOK_{uuid.uuid4().hex[:12]}"


class DataMaskingEngine:
    """Applies interchangeable masking strategies."""

    STRATEGIES = {
        "partial": PartialMask(),
        "full": FullMask(),
        "hash": HashMask(),
        "tokenize": TokenizeMask(),
    }

    @classmethod
    def mask(cls, value: str, strategy: str = "partial") -> str:
        masker = cls.STRATEGIES.get(strategy)
        if not masker:
            raise ValueError(f"Unknown masking strategy: {strategy}")
        return masker.mask(value)
