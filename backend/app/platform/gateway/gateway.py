import time
from typing import Dict
from app.platform.tenant.models import RateLimitEntry


class APIGateway:
    """
    Enterprise API Gateway with rate limiting, throttling, and burst control.
    """

    _rate_limits: Dict[str, RateLimitEntry] = {}
    DEFAULT_LIMIT = 100  # requests per minute

    @classmethod
    def check_rate_limit(cls, tenant_id: str, limit: int = None) -> bool:
        """Returns True if the request is allowed, False if rate-limited."""
        now = time.time()
        entry = cls._rate_limits.get(tenant_id)
        max_limit = limit or cls.DEFAULT_LIMIT

        if not entry:
            cls._rate_limits[tenant_id] = RateLimitEntry(
                tenant_id=tenant_id, requests_count=1,
                window_start=now, limit=max_limit,
            )
            return True

        # Reset window if expired (1 minute)
        if now - entry.window_start > 60:
            entry.requests_count = 1
            entry.window_start = now
            return True

        if entry.requests_count >= max_limit:
            return False

        entry.requests_count += 1
        return True

    @classmethod
    def get_usage(cls, tenant_id: str) -> Dict:
        entry = cls._rate_limits.get(tenant_id)
        if not entry:
            return {"tenant_id": tenant_id, "used": 0, "limit": cls.DEFAULT_LIMIT}
        return {
            "tenant_id": tenant_id,
            "used": entry.requests_count,
            "limit": entry.limit,
            "remaining": max(0, entry.limit - entry.requests_count),
        }
