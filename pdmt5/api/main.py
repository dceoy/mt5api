"""FastAPI application instance and lifecycle management."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

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
