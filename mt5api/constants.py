"""Application-wide constants."""

from __future__ import annotations

import os


def _normalize_api_router_prefix(raw_prefix: str | None) -> str:
    """Normalize the API router prefix from environment configuration.

    Args:
        raw_prefix: Raw prefix string from ``API_ROUTER_PREFIX``.

    Returns:
        Prefix suitable for FastAPI router mounting.
    """
    if raw_prefix is None:
        return ""

    prefix = raw_prefix.strip().strip("/")
    if not prefix:
        return ""

    return f"/{prefix}"


API_ROUTER_PREFIX = _normalize_api_router_prefix(os.getenv("API_ROUTER_PREFIX"))
