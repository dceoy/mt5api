"""Application-wide constants and environment-backed configuration helpers."""

from __future__ import annotations

import os

API_TITLE = "MT5 REST API"
API_DESCRIPTION = (
    "REST API for MetaTrader 5 data access. "
    "Provides read-only access to market data, "
    "account information, and trading history via HTTP endpoints."
)
API_VERSION = "1.0.0"
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"
API_OPENAPI_URL = "/openapi.json"
API_APP_IMPORT = "mt5api.main:app"
API_KEY_HEADER_NAME = "X-API-Key"
API_KEY_SECURITY_SCHEME_NAME = "APIKeyHeader"

ENV_API_HOST = "API_HOST"
ENV_API_PORT = "API_PORT"
ENV_API_LOG_LEVEL = "API_LOG_LEVEL"
ENV_API_RATE_LIMIT = "API_RATE_LIMIT"
ENV_API_CORS_ORIGINS = "API_CORS_ORIGINS"
ENV_API_ROUTER_PREFIX = "API_ROUTER_PREFIX"
ENV_MT5_API_KEY = "MT5_API_KEY"

DEFAULT_API_HOST = "0.0.0.0"  # noqa: S104
DEFAULT_API_PORT = 8000
DEFAULT_API_LOG_LEVEL = "INFO"
DEFAULT_API_RATE_LIMIT = 100
DEFAULT_API_CORS_ORIGINS = "*"
DEFAULT_API_ROUTER_PREFIX = ""
MAX_API_PORT = 65535


def normalize_api_router_prefix(raw_prefix: str | None) -> str:
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


def get_configured_api_host() -> str:
    """Get the configured API host.

    Returns:
        Host address for binding the API server.
    """
    return os.getenv(ENV_API_HOST, DEFAULT_API_HOST)


def get_configured_api_port() -> str | None:
    """Get the configured API port string.

    Returns:
        Raw port string from the environment, or ``None`` if unset.
    """
    return os.getenv(ENV_API_PORT)


def get_configured_api_log_level() -> str:
    """Get the configured API log level.

    Returns:
        Log level string from configuration.
    """
    return os.getenv(ENV_API_LOG_LEVEL, DEFAULT_API_LOG_LEVEL)


def get_configured_api_rate_limit() -> str:
    """Get the configured API rate limit string.

    Returns:
        Raw per-minute rate-limit string from configuration.
    """
    return os.getenv(ENV_API_RATE_LIMIT, str(DEFAULT_API_RATE_LIMIT))


def get_configured_api_cors_origins() -> str:
    """Get the configured CORS origins string.

    Returns:
        Raw CORS origins configuration string.
    """
    return os.getenv(ENV_API_CORS_ORIGINS, DEFAULT_API_CORS_ORIGINS)


def get_configured_api_router_prefix() -> str:
    """Get the configured API router prefix.

    Returns:
        Normalized router prefix for mounting API routes.
    """
    return normalize_api_router_prefix(
        os.getenv(ENV_API_ROUTER_PREFIX, DEFAULT_API_ROUTER_PREFIX)
    )


def get_configured_mt5_api_key() -> str | None:
    """Get the configured MT5 API key, if any.

    Returns:
        MT5 API key string, or ``None`` when authentication is disabled.
    """
    return os.getenv(ENV_MT5_API_KEY) or None
