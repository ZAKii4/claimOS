import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config.settings import get_settings

logger = logging.getLogger("claimOS.security")

# In a real enterprise system, RS256 with a private/public keypair would be used.
# For demonstration without external key injection, we use HS256.
_settings = get_settings()
ALGORITHM = _settings.JWT_ALGORITHM

if _settings.SECRET_KEY:
    SECRET_KEY = _settings.SECRET_KEY
else:
    # No fake/hardcoded secret: generate a real random key so tokens are at
    # least genuinely unforgeable, but be explicit that this is a dev-only
    # fallback — it changes on every restart, invalidating all issued tokens.
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning(
        "SECRET_KEY is not set — generated an ephemeral per-process JWT signing "
        "key. All tokens will be invalidated on restart. Set the SECRET_KEY "
        "environment variable for any persistent/production deployment."
    )


class JWTManager:
    """
    Handles JWT access and refresh tokens.
    """
    def __init__(self):
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7
        self.blacklisted_tokens = set() # Mock database for revoked tokens

    def create_access_token(self, subject: str, extra_claims: dict[str, Any] = None) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid.uuid4())}
        if extra_claims:
            to_encode.update(extra_claims)

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, subject: str) -> str:
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "exp": expire, "sub": str(subject), "type": "refresh", "jti": str(uuid.uuid4())
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> dict[str, Any] | None:
        if token in self.blacklisted_tokens:
            return None
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def revoke_token(self, token: str):
        self.blacklisted_tokens.add(token)

jwt_manager = JWTManager()
