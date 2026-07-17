import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class APIKeyManager:
    """
    Manages API Keys for external integrations (M2M authentication).
    """
    def __init__(self):
        self.keys: Dict[str, Dict[str, Any]] = {}
        
    def generate_key(self, tenant_id: str, name: str, scopes: list[str], expire_days: int = 365) -> str:
        # Format: cos_live_randomstring
        raw_key = f"cos_live_{secrets.token_urlsafe(32)}"
        
        self.keys[raw_key] = {
            "tenant_id": tenant_id,
            "name": name,
            "scopes": scopes,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=expire_days)
        }
        return raw_key
        
    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        key_data = self.keys.get(api_key)
        if not key_data:
            return None
            
        if datetime.utcnow() > key_data["expires_at"]:
            return None
            
        return key_data
        
    def revoke_key(self, api_key: str) -> bool:
        if api_key in self.keys:
            del self.keys[api_key]
            return True
        return False

api_key_manager = APIKeyManager()
