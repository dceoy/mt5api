"""FastAPI application instance and lifecycle management."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware

from .auth import is_auth_enabled
from .dependencies import shutdown_mt5_client
from .middleware import add_middleware
from .routers import account, health, history, market, symbols

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
    log_level = os.getenv("API_LOG_LEVEL", "INFO").upper()

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
    raw_origins = os.getenv("API_CORS_ORIGINS", "*")
    if raw_origins.strip() == "*":
        return ["*"]

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def _strip_auth_from_openapi(openapi_schema: dict[str, Any]) -> None:
    """Remove API key requirements from OpenAPI when auth is disabled."""
    openapi_schema.pop("security", None)

    components = openapi_schema.get("components")
    if isinstance(components, dict):
        security_schemes = components.get("securitySchemes")
        if isinstance(security_schemes, dict):
            security_schemes.pop("APIKeyHeader", None)
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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Manage application lifespan (startup and shutdown).

    Args:
        app: FastAPI application instance (unused but required by FastAPI).

    Yields:
        None
    """
    # Startup
    logger.info("Starting MT5 REST API...")

    # Note: MT5 client is initialized lazily on first request via dependency
    # This avoids blocking startup if MT5 is not available
    await asyncio.sleep(0)  # Make function truly async

    yield

    # Shutdown
    logger.info("Shutting down MT5 REST API...")
    shutdown_mt5_client()
    logger.info("MT5 connection closed")


# Create FastAPI application
app = FastAPI(
    title="MT5 REST API",
    description=(
        "REST API for MetaTrader 5 data access. "
        "Provides read-only access to market data, "
        "account information, and trading history via HTTP endpoints."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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
app.include_router(health.router)
app.include_router(symbols.router)
app.include_router(market.router)
app.include_router(account.router)
app.include_router(history.router)

logger.info("MT5 REST API initialized")
