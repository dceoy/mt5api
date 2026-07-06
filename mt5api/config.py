"""Environment-backed configuration helpers."""

from __future__ import annotations

import os
import re

from .constants import (
    DEFAULT_API_HOST,
    DEFAULT_API_LOG_LEVEL,
    DEFAULT_API_PORT,
    DEFAULT_API_ROUTER_PREFIX,
    DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    ENV_MT5API_HOST,
    ENV_MT5API_LOG_LEVEL,
    ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    ENV_MT5API_PORT,
    ENV_MT5API_ROUTER_PREFIX,
    ENV_MT5API_SECRET_KEY,
    MAX_API_PORT,
)

_VALID_API_ROUTER_PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*$")
_VALID_UVICORN_LOG_LEVELS = {"critical", "error", "warning", "info", "debug", "trace"}
_LOGGING_LOG_LEVEL_BY_API_LEVEL = {
    "critical": "CRITICAL",
    "error": "ERROR",
    "warning": "WARNING",
    "info": "INFO",
    "debug": "DEBUG",
    "trace": "DEBUG",
}
_INVALID_MT5API_PORT_ERROR = "Invalid MT5API_PORT"
_INVALID_MT5API_LOG_LEVEL_ERROR = "Invalid MT5API_LOG_LEVEL"
_INVALID_MT5API_ROUTER_PREFIX_ERROR = "Invalid MT5API_ROUTER_PREFIX"
_INVALID_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS_ERROR = (
    "Invalid MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS"
)


def normalize_api_router_prefix(raw_prefix: str | None) -> str:
    """Normalize the API router prefix from environment configuration.

    Args:
        raw_prefix: Raw prefix string from ``MT5API_ROUTER_PREFIX``.

    Returns:
        Prefix suitable for FastAPI router mounting.

    Raises:
        ValueError: If the configured prefix contains invalid path characters.
    """
    if raw_prefix is None:
        return ""

    prefix = raw_prefix.strip().strip("/")
    if not prefix:
        return ""

    if not _VALID_API_ROUTER_PREFIX_PATTERN.fullmatch(prefix):
        raise ValueError(_INVALID_MT5API_ROUTER_PREFIX_ERROR)

    return f"/{prefix}"


def get_configured_api_host() -> str:
    """Get the configured API host.

    Returns:
        Host address for binding the API server.
    """
    return os.getenv(ENV_MT5API_HOST, DEFAULT_API_HOST)


def get_configured_api_port() -> int:
    """Get the configured API port.

    Returns:
        Port number for the API server.

    Raises:
        ValueError: If the configured port is not an integer in the TCP port range.
    """
    raw_port = os.getenv(ENV_MT5API_PORT)
    if raw_port is None:
        return DEFAULT_API_PORT

    try:
        port = int(raw_port)
    except ValueError as error:
        raise ValueError(_INVALID_MT5API_PORT_ERROR) from error

    if not 1 <= port <= MAX_API_PORT:
        raise ValueError(_INVALID_MT5API_PORT_ERROR)

    return port


def get_configured_api_log_level() -> str:
    """Get the configured API log level.

    Returns:
        Valid uvicorn log level string from configuration.

    Raises:
        ValueError: If the configured log level is unsupported.
    """
    log_level = os.getenv(ENV_MT5API_LOG_LEVEL, DEFAULT_API_LOG_LEVEL).strip().lower()
    if log_level not in _VALID_UVICORN_LOG_LEVELS:
        raise ValueError(_INVALID_MT5API_LOG_LEVEL_ERROR)
    return log_level


def get_configured_python_log_level() -> str:
    """Get a stdlib logging-compatible log level for the API logger.

    Returns:
        Python logging level name derived from the configured API log level.
    """
    return _LOGGING_LOG_LEVEL_BY_API_LEVEL[get_configured_api_log_level()]


def get_configured_api_router_prefix() -> str:
    """Get the configured API router prefix.

    Returns:
        Normalized router prefix for mounting API routes.
    """
    return normalize_api_router_prefix(
        os.getenv(ENV_MT5API_ROUTER_PREFIX, DEFAULT_API_ROUTER_PREFIX)
    )


def get_configured_max_market_book_subscriptions() -> int:
    """Get the configured market-book subscription limit.

    Returns:
        Positive maximum number of tracked market-book subscriptions.

    Raises:
        ValueError: If the configured limit is not a positive integer.
    """
    raw_limit = os.getenv(
        ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
        str(DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS),
    )

    try:
        limit = int(raw_limit)
    except ValueError as error:
        raise ValueError(_INVALID_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS_ERROR) from error

    if limit < 1:
        raise ValueError(_INVALID_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS_ERROR)

    return limit


def get_configured_mt5api_secret_key() -> str | None:
    """Get the configured MT5 API secret key, if any.

    Returns:
        MT5 API secret key string, or ``None`` when authentication is disabled.
    """
    return os.getenv(ENV_MT5API_SECRET_KEY) or None
