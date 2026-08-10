"""FastAPI application instance and lifecycle management."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, cast

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
    from collections.abc import AsyncGenerator, Iterator


def _as_dict(value: object) -> dict[str, Any] | None:
    """Return a typed dictionary after checking a dynamic OpenAPI value."""
    if not isinstance(value, dict):
        return None
    return cast("dict[str, Any]", value)


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


def _iter_openapi_operations(
    openapi_schema: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    """Yield operation mappings from an OpenAPI schema.

    Yields:
        Individual HTTP operation mappings.
    """
    paths = _as_dict(openapi_schema.get("paths", {}))
    if paths is None:
        return
    for methods_value in paths.values():
        methods = _as_dict(methods_value)
        if methods is None:
            continue
        for operation_value in methods.values():
            operation = _as_dict(operation_value)
            if operation is not None:
                yield operation


def _strip_auth_from_openapi(openapi_schema: dict[str, Any]) -> None:
    """Remove API key requirements from OpenAPI when auth is disabled."""
    openapi_schema.pop("security", None)
    components = _as_dict(openapi_schema.get("components", {}))
    if components is not None:
        security_schemes = _as_dict(components.get("securitySchemes", {}))
        if security_schemes is not None:
            security_schemes.pop(API_KEY_SECURITY_SCHEME_NAME, None)
            if not security_schemes:
                components.pop("securitySchemes", None)
    for operation in _iter_openapi_operations(openapi_schema):
        operation.pop("security", None)


def _patch_validation_error_responses(openapi_schema: dict[str, Any]) -> None:
    """Advertise RFC 7807 Problem Details for request validation failures."""
    components = _as_dict(openapi_schema.setdefault("components", {}))
    if components is None:
        return
    schemas = _as_dict(components.setdefault("schemas", {}))
    if schemas is None:
        return
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
    for operation in _iter_openapi_operations(openapi_schema):
        responses = operation.get("responses")
        responses = _as_dict(
            cast("object", responses),  # pyright: ignore[reportUnknownArgumentType]
        )
        if responses is not None and "422" in responses:
            responses["422"] = error_response


def _supports_format_query(operation: dict[str, Any]) -> bool:
    """Return whether an OpenAPI operation exposes the shared format query."""
    parameters = operation.get("parameters", [])
    if not isinstance(parameters, list):
        return False
    parameters = cast("list[object]", parameters)
    return any(
        (parameter := _as_dict(parameter_value)) is not None
        and parameter.get("in") == "query"
        and parameter.get("name") == "format"
        for parameter_value in parameters
    )


def _patch_parquet_success_responses(openapi_schema: dict[str, Any]) -> None:
    """Advertise Parquet for operations using the shared format dependency."""
    parquet_schema = {"schema": {"type": "string", "format": "binary"}}
    for operation in _iter_openapi_operations(openapi_schema):
        if not _supports_format_query(operation):
            continue
        responses = operation.get("responses")
        responses = _as_dict(
            cast("object", responses),  # pyright: ignore[reportUnknownArgumentType]
        )
        if responses is None:
            continue
        success = _as_dict(responses.get("200"))
        if success is None:
            continue
        content = _as_dict(success.setdefault("content", {}))
        if content is not None:
            content.setdefault("application/parquet", parquet_schema)


def _build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Build OpenAPI schema for the current authentication mode.

    Returns:
        Cached or newly generated OpenAPI schema.
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
    _patch_validation_error_responses(openapi_schema)
    _patch_parquet_success_responses(openapi_schema)
    app.openapi_schema = openapi_schema
    return openapi_schema


def _custom_openapi() -> dict[str, Any]:
    """Build OpenAPI schema for the current application instance.

    Returns:
        Cached or newly generated OpenAPI schema.
    """
    return _build_openapi_schema(app)


_configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Yields:
        Control to FastAPI while the application is running.
    """
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
