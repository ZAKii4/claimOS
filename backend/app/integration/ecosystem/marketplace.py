import hashlib
import json
from typing import Dict, List, Optional
from app.integration.core.models import MarketplaceExtension


class MarketplaceManager:
    """Manages safe installation of 3rd-party extensions with signature verification."""

    _catalog: Dict[str, MarketplaceExtension] = {}
    _installed: Dict[str, MarketplaceExtension] = {}

    @classmethod
    def publish_to_catalog(cls, extension: MarketplaceExtension, private_key_stub: str = "secret"):
        """Publish an extension to the catalog and generate its signature."""
        payload = f"{extension.id}:{extension.version}:{private_key_stub}"
        extension.signature = hashlib.sha256(payload.encode()).hexdigest()
        cls._catalog[extension.id] = extension

    @classmethod
    def get_catalog(cls) -> List[MarketplaceExtension]:
        return list(cls._catalog.values())

    @classmethod
    def install(cls, extension_id: str, public_key_stub: str = "secret") -> bool:
        """Verify signature and install."""
        extension = cls._catalog.get(extension_id)
        if not extension:
            return False

        # Verify signature
        expected_payload = f"{extension.id}:{extension.version}:{public_key_stub}"
        expected_sig = hashlib.sha256(expected_payload.encode()).hexdigest()

        if expected_sig != extension.signature:
            raise ValueError("Invalid signature: Extension may be tampered with.")

        extension.installed = True
        cls._installed[extension_id] = extension
        return True

    @classmethod
    def get_installed(cls) -> List[MarketplaceExtension]:
        return list(cls._installed.values())
