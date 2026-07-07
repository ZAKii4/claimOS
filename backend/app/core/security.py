"""
Security utilities — MVP stub.

For the MVP, authentication is bypassed: every request is attributed to
a default system operator. This module is designed to be replaced by a
proper JWT / OAuth2 integration without impacting the rest of the codebase.
"""

from uuid import UUID


# ---------------------------------------------------------------------------
# Placeholder — replace with real auth in production
# ---------------------------------------------------------------------------

_SYSTEM_OPERATOR_ID: str = "SYSTEM"


def get_current_operator_id() -> str:
    """
    Return the ID of the currently authenticated operator.

    MVP stub: always returns the SYSTEM operator.
    In production, this will decode a JWT token from the request.
    """
    return _SYSTEM_OPERATOR_ID
