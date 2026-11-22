"""API key authentication for REST API endpoints."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import get_configured_mt5api_secret_key
from .constants import API_KEY_HEADER_NAME

# API key security scheme
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
# Auth mode is fixed for the lifetime of the process.
_API_KEY: str | None = get_configured_mt5api_secret_key()


def get_api_key() -> str | None:
    """Get the API key configured at startup, if any.

    Returns:
        API key string from ``MT5API_SECRET_KEY``, or ``None`` if it is missing.
    """
    return _API_KEY


def is_auth_enabled() -> bool:
    """Return whether API key authentication is enabled."""
    return _API_KEY is not None


def verify_api_key(
    api_key_header_value: Annotated[str | None, Security(api_key_header)],
) -> str | None:
    """Verify API key from request header.

    Args:
        api_key_header_value: API key from the configured request header.

    Returns:
        Verified API key.

    Raises:
        HTTPException: 401 if API key is missing or invalid; 503 if no key is
            configured.
    """
    expected_key = get_api_key()
    if expected_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5API_SECRET_KEY is required",
        )

    if not api_key_header_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "/errors/unauthorized",
                "title": "Authentication Required",
                "status": 401,
                "detail": f"Missing API key. Provide {API_KEY_HEADER_NAME} header.",
                "instance": None,
            },
        )

    if not hmac.compare_digest(api_key_header_value, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "/errors/unauthorized",
                "title": "Authentication Failed",
                "status": 401,
                "detail": "Invalid API key.",
                "instance": None,
            },
        )

    return api_key_header_value
