"""FastAPI application instance and lifecycle management."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from .auth import is_auth_enabled
from .config import (
    get_configured_api_log_level,
    get_configured_api_router_prefix,
    get_configured_max_market_book_subscriptions,
)
from .constants import (
    ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
    API_DESCRIPTION,
    API_DOCS_URL,
    API_KEY_SECURITY_SCHEME_NAME,
    API_OPENAPI_URL,
    API_REDOC_URL,
    API_TITLE,
    API_VERSION,
    MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY,
    MAX_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
)
from .dependencies import release_market_book_subscriptions, shutdown_mt5_client
from .middleware import add_middleware
from .routers import (
    account,
    calc,
    connection,
    health,
    history,
    market,
    symbols,
    trading,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class _JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def _configure_logging() -> None:
    """Configure structured logging for the API."""
    log_level = get_configured_api_log_level().upper()

    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def _strip_auth_from_openapi(openapi_schema: dict[str, Any]) -> None:
    """Remove API key requirements from OpenAPI when auth is disabled."""
    openapi_schema.pop("security", None)

    components = openapi_schema.get("components")
    if isinstance(components, dict):
        security_schemes = components.get("securitySchemes")
        if isinstance(security_schemes, dict):
            security_schemes.pop(API_KEY_SECURITY_SCHEME_NAME, None)
            if not security_schemes:
                components.pop("securitySchemes", None)

    for methods in openapi_schema.get("paths", {}).values():
        if not isinstance(methods, dict):
            continue
        for operation in methods.values():
            if isinstance(operation, dict):
                operation.pop("security", None)


def _build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Build OpenAPI schema for the current authentication mode.

    Returns:
        OpenAPI schema for the current auth configuration.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    if not is_auth_enabled():
        _strip_auth_from_openapi(openapi_schema)

    app.openapi_schema = openapi_schema
    return openapi_schema


def _custom_openapi() -> dict[str, Any]:
    """Build OpenAPI schema for the current application instance.

    Returns:
        OpenAPI schema for the application.
    """
    return _build_openapi_schema(app)


_configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan (startup and shutdown).

    Args:
        app: FastAPI application instance (unused but required by FastAPI).

    Yields:
        None
    """
    # Startup
    logger.info("Starting MT5 REST API...")
    setattr(app.state, ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY, set())
    setattr(app.state, MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
    setattr(
        app.state,
        MAX_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
        get_configured_max_market_book_subscriptions(),
    )

    # Note: MT5 client is initialized lazily on first request via dependency
    # This avoids blocking startup if MT5 is not available
    await asyncio.sleep(0)  # Make function truly async

    yield

    # Shutdown
    logger.info("Shutting down MT5 REST API...")
    try:
        await release_market_book_subscriptions(app)
    finally:
        shutdown_mt5_client()
    logger.info("MT5 connection closed")


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url=API_DOCS_URL,
    redoc_url=API_REDOC_URL,
    openapi_url=API_OPENAPI_URL,
)
app.openapi = _custom_openapi

# Add middleware
add_middleware(app)

# Include routers
router_prefix = get_configured_api_router_prefix()
app.include_router(health.router, prefix=router_prefix)
app.include_router(symbols.router, prefix=router_prefix)
app.include_router(market.router, prefix=router_prefix)
app.include_router(account.router, prefix=router_prefix)
app.include_router(history.router, prefix=router_prefix)
app.include_router(calc.router, prefix=router_prefix)
app.include_router(trading.router, prefix=router_prefix)
app.include_router(connection.router, prefix=router_prefix)

logger.info("MT5 REST API initialized")
