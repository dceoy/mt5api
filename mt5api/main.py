"""FastAPI application instance and lifecycle management."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware

from .auth import is_auth_enabled
from .config import (
    get_configured_api_cors_origins,
    get_configured_api_log_level,
    get_configured_api_router_prefix,
)
from .constants import (
    API_DESCRIPTION,
    API_DOCS_URL,
    API_KEY_SECURITY_SCHEME_NAME,
    API_OPENAPI_URL,
    API_REDOC_URL,
    API_TITLE,
    API_VERSION,
    DEFAULT_API_CORS_ORIGINS,
)
from .dependencies import run_in_threadpool, shutdown_mt5_client
from .middleware import add_middleware
from .routers import account, calc, health, history, market, symbols, trading

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


def _get_cors_origins() -> list[str]:
    """Get CORS origins from environment.

    Returns:
        List of allowed origins.
    """
    raw_origins = get_configured_api_cors_origins()
    if raw_origins.strip() == DEFAULT_API_CORS_ORIGINS:
        return [DEFAULT_API_CORS_ORIGINS]

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


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
_ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY = "active_market_book_subscriptions"
_MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY = "market_book_cleanup_client"


async def _release_market_book_subscriptions(app: FastAPI) -> None:
    """Release active market-book subscriptions before shutting down MT5."""
    subscriptions = getattr(
        app.state,
        _ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
        None,
    )
    if not isinstance(subscriptions, set) or not subscriptions:
        return

    mt5_client = getattr(app.state, _MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
    if mt5_client is None:
        logger.warning("Active market-book subscriptions found without cleanup client")
        subscriptions.clear()
        setattr(app.state, _MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
        return

    for symbol in tuple(sorted(subscriptions)):
        await run_in_threadpool(mt5_client.market_book_release, symbol=symbol)

    subscriptions.clear()
    setattr(app.state, _MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)


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
    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None

    # Note: MT5 client is initialized lazily on first request via dependency
    # This avoids blocking startup if MT5 is not available
    await asyncio.sleep(0)  # Make function truly async

    yield

    # Shutdown
    logger.info("Shutting down MT5 REST API...")
    try:
        await _release_market_book_subscriptions(app)
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

logger.info("MT5 REST API initialized")
