"""FastAPI application instance and lifecycle management."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from .auth import is_auth_enabled
from .config import (
    get_configured_api_router_prefix,
    get_configured_max_market_book_subscriptions,
    get_configured_python_log_level,
)
from .constants import (
    API_DESCRIPTION,
    API_DOCS_URL,
    API_KEY_SECURITY_SCHEME_NAME,
    API_OPENAPI_URL,
    API_REDOC_URL,
    API_TITLE,
    API_VERSION,
)
from .dependencies import (
    initialize_mt5_runtime_state,
    release_market_book_subscriptions,
    shutdown_mt5_client,
)
from .middleware import add_middleware
from .models import ErrorResponse
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
    log_level = get_configured_python_log_level()

    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def _strip_auth_from_openapi(openapi_schema: dict[str, Any]) -> None:
    """Remove API key requirements from OpenAPI when auth is disabled."""
    openapi_schema.pop("security", None)

    components = openapi_schema.get("components", {})
    if isinstance(components, dict):
        security_schemes = components.get("securitySchemes", {})
        if isinstance(security_schemes, dict):
            security_schemes.pop(API_KEY_SECURITY_SCHEME_NAME, None)
            if not security_schemes:
                components.pop("securitySchemes", None)

    paths = openapi_schema.get("paths", {})
    if not isinstance(paths, dict):
        return
    for methods in paths.values():
        if not isinstance(methods, dict):
            continue
        for operation in methods.values():
            if isinstance(operation, dict):
                operation.pop("security", None)


def _patch_validation_error_responses(openapi_schema: dict[str, Any]) -> None:
    """Advertise RFC 7807 Problem Details for request validation failures."""
    components = openapi_schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas["ErrorResponse"] = ErrorResponse.model_json_schema(
        ref_template="#/components/schemas/{model}",
    )
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)

    error_response = {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
            },
        },
    }

    paths = openapi_schema.get("paths", {})
    if not isinstance(paths, dict):
        return
    for methods in paths.values():
        if not isinstance(methods, dict):
            continue
        for operation in methods.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if isinstance(responses, dict) and "422" in responses:
                responses["422"] = error_response


def _patch_parquet_success_responses(openapi_schema: dict[str, Any]) -> None:
    """Advertise Parquet for operations using the shared format dependency."""
    paths = openapi_schema.get("paths", {})
    if not isinstance(paths, dict):
        return
    parquet_schema = {"schema": {"type": "string", "format": "binary"}}
    for methods in paths.values():
        if not isinstance(methods, dict):
            continue
        for operation in methods.values():
            if not isinstance(operation, dict):
                continue
            parameters = operation.get("parameters", [])
            if not isinstance(parameters, list):
                continue
            supports_format = any(
                isinstance(parameter, dict)
                and parameter.get("in") == "query"
                and parameter.get("name") == "format"
                for parameter in parameters
            )
            if not supports_format:
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            success = responses.get("200")
            if not isinstance(success, dict):
                continue
            content = success.setdefault("content", {})
            if isinstance(content, dict):
                content.setdefault("application/parquet", parquet_schema)


def _build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Build OpenAPI schema for the current authentication mode."""
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
    _patch_validation_error_responses(openapi_schema)
    _patch_parquet_success_responses(openapi_schema)

    app.openapi_schema = openapi_schema
    return openapi_schema


def _custom_openapi() -> dict[str, Any]:
    """Build OpenAPI schema for the current application instance."""
    return _build_openapi_schema(app)


_configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    logger.info("Starting MT5 REST API...")
    state = initialize_mt5_runtime_state(
        app,
        max_market_book_subscriptions=get_configured_max_market_book_subscriptions(),
    )

    yield

    logger.info("Shutting down MT5 REST API...")
    try:
        await release_market_book_subscriptions(state)
    finally:
        shutdown_mt5_client(state)
    logger.info("MT5 connection closed")


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

add_middleware(app)

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
