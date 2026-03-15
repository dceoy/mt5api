"""API key authentication for REST API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .config import get_configured_mt5_api_key
from .constants import API_KEY_HEADER_NAME

# API key security scheme
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
# Auth mode is fixed for the lifetime of the process.
_API_KEY: str | None = get_configured_mt5_api_key()


def get_api_key() -> str | None:
    """Get the API key configured at startup, if any.

    Returns:
        API key string from ``MT5_API_KEY``, or ``None`` if authentication is
        disabled.
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
        Verified API key when authentication is enabled, otherwise ``None``.

    Raises:
        HTTPException: 401 if API key is missing or invalid.
    """
    expected_key = get_api_key()
    if expected_key is None:
        return None

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

    if api_key_header_value != expected_key:
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
