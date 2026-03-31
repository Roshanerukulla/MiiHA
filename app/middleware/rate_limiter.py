"""
Rate Limiting Middleware (Feature 9)

Uses slowapi to apply per-user rate limits to expensive endpoints.
Rate limit key is extracted from the JWT bearer token (user email).
"""
from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.jwt import decode_access_token
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_user_identifier(request: Request) -> str:
    """
    Extract a unique rate-limit key from the request.

    Attempts to decode the JWT bearer token and return the user email.
    Falls back to the client IP address if no valid token is present.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        try:
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return payload["sub"]  # email
        except Exception:
            pass
    return get_remote_address(request)


# Global limiter instance — import this in main.py and individual routers
limiter = Limiter(key_func=_get_user_identifier)
