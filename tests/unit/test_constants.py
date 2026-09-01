"""Tests for application-wide constants."""

from __future__ import annotations

from importlib.metadata import version

from mt5api.constants import (
    API_APP_IMPORT,
    API_DESCRIPTION,
    API_DOCS_URL,
    API_KEY_HEADER_NAME,
    API_KEY_SECURITY_SCHEME_NAME,
    API_OPENAPI_URL,
    API_REDOC_URL,
    API_TITLE,
    API_VERSION,
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
    MT5_RUNTIME_STATE_KEY,
)


def test_api_metadata_constants_match_package_contract() -> None:
    """API metadata constants expose the package's public contract."""
    assert API_TITLE == "MT5 REST API"
    assert API_DESCRIPTION == (
        "REST API for MetaTrader 5 data access and non-executing terminal utilities. "
        "Provides market data, account information, trading history, calculations, "
        "and safe operational endpoints via HTTP."
    )
    assert version("mt5api") == API_VERSION
    assert API_DOCS_URL == "/docs"
    assert API_REDOC_URL == "/redoc"
    assert API_OPENAPI_URL == "/openapi.json"
    assert API_APP_IMPORT == "mt5api.main:app"
    assert API_KEY_HEADER_NAME == "X-API-Key"
    assert API_KEY_SECURITY_SCHEME_NAME == "APIKeyHeader"
    assert MT5_RUNTIME_STATE_KEY == "mt5_runtime"


def test_configuration_constants_match_environment_contract() -> None:
    """Configuration constants expose stable environment names and defaults."""
    assert (
        ENV_MT5API_HOST,
        ENV_MT5API_PORT,
        ENV_MT5API_LOG_LEVEL,
        ENV_MT5API_ROUTER_PREFIX,
        ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
        ENV_MT5API_SECRET_KEY,
    ) == (
        "MT5API_HOST",
        "MT5API_PORT",
        "MT5API_LOG_LEVEL",
        "MT5API_ROUTER_PREFIX",
        "MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS",
        "MT5API_SECRET_KEY",
    )
    assert DEFAULT_API_HOST == "0.0.0.0"  # noqa: S104
    assert (
        DEFAULT_API_PORT,
        DEFAULT_API_LOG_LEVEL,
        DEFAULT_API_ROUTER_PREFIX,
        DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS,
        MAX_API_PORT,
    ) == (8000, "INFO", "", 100, 65535)
