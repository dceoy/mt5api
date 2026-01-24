"""API key authentication for REST API endpoints."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    """Get API key from environment variable.

    Returns:
        API key string from MT5_API_KEY environment variable.

    Raises:
        RuntimeError: If MT5_API_KEY environment variable is not set.
    """
    api_key = os.getenv("MT5_API_KEY")
    if not api_key:
        error_message = (
            "MT5_API_KEY environment variable not set. "
            "Please set it to enable API authentication."
        )
        raise RuntimeError(error_message)
    return api_key


def verify_api_key(
    api_key_header_value: Annotated[str | None, Security(api_key_header)],
) -> str:
    """Verify API key from request header.

    Args:
        api_key_header_value: API key from X-API-Key header.

    Returns:
        Verified API key.

    Raises:
        HTTPException: 401 if API key is missing or invalid.
    """
    expected_key = get_api_key()

    if not api_key_header_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "/errors/unauthorized",
                "title": "Authentication Required",
                "status": 401,
                "detail": "Missing API key. Provide X-API-Key header.",
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
