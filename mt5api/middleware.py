"""Error handling and logging middleware."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, cast

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pdmt5.mt5 import Mt5RuntimeError
from pydantic import ValidationError

from .models import ErrorResponse

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi import FastAPI
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.responses import Response

logger = logging.getLogger(__name__)


def _format_validation_error_location(location: Sequence[Any]) -> str:
    """Format a Pydantic error location for display.

    Args:
        location: Pydantic validation error location tuple.

    Returns:
        Human-readable field path without the request-body prefix.
    """
    parts = [str(part) for part in location if str(part) != "body"]
    return ".".join(parts) if parts else "request"


def _format_request_validation_detail(exc: RequestValidationError) -> str:
    """Build a sanitized validation detail string without echoing request input.

    Args:
        exc: FastAPI request validation error.

    Returns:
        Validation summary containing field paths and messages only.
    """
    details: list[str] = []
    for error in exc.errors():
        location = _format_validation_error_location(error.get("loc", ()))
        message = str(error.get("msg", "Invalid value"))
        details.append(f"{location}: {message}")
    return "; ".join(details) if details else "Request validation failed"


def _create_error_response(
    error_type: str,
    title: str,
    status_code: int,
    detail: str,
    instance: str,
) -> JSONResponse:
    """Create a RFC 7807 Problem Details error response.

    Args:
        error_type: Error type URI (e.g., "/errors/mt5-error").
        title: Short error summary.
        status_code: HTTP status code.
        detail: Detailed error explanation.
        instance: Request URI that caused the error.

    Returns:
        JSONResponse with error details.
    """
    error = ErrorResponse(
        type=error_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
    )
    return JSONResponse(status_code=status_code, content=error.model_dump())


async def error_handler_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Handle errors and convert to RFC 7807 Problem Details responses.

    Error type mapping:
        - Mt5RuntimeError -> 503 Service Unavailable
        - ValidationError -> 400 Bad Request
        - ValueError -> 400 Bad Request
        - RuntimeError -> 503 Service Unavailable
        - Exception -> 500 Internal Server Error

    Args:
        request: FastAPI request object.
        call_next: Next middleware or endpoint handler.

    Returns:
        Response with error details in RFC 7807 format.
    """
    try:
        return await call_next(request)
    except Mt5RuntimeError as e:
        logger.exception("MT5 error")
        return _create_error_response(
            "/errors/mt5-error",
            "MT5 Terminal Error",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(e),
            str(request.url),
        )
    except ValidationError as e:
        logger.warning("Validation error: %s", e)
        return _create_error_response(
            "/errors/validation-error",
            "Request Validation Failed",
            status.HTTP_400_BAD_REQUEST,
            str(e),
            str(request.url),
        )
    except ValueError as e:
        logger.warning("Invalid input: %s", e)
        return _create_error_response(
            "/errors/invalid-input",
            "Invalid Input",
            status.HTTP_400_BAD_REQUEST,
            str(e),
            str(request.url),
        )
    except RuntimeError as e:
        logger.exception("Runtime error")
        return _create_error_response(
            "/errors/runtime-error",
            "Runtime Error",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(e),
            str(request.url),
        )
    except Exception:
        logger.exception("Unexpected error")
        return _create_error_response(
            "/errors/internal-error",
            "Internal Server Error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred",
            str(request.url),
        )


async def logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Log all requests and responses with timing information.

    Args:
        request: FastAPI request object.
        call_next: Next middleware or endpoint handler.

    Returns:
        Response from endpoint handler.
    """
    start_time = time.time()

    # Log request
    logger.info(
        "Request: %s %s params=%s from %s",
        request.method,
        request.url.path,
        dict(request.query_params),
        request.client.host if request.client else "unknown",
    )

    # Process request
    response = await call_next(request)

    # Log response with timing
    process_time = time.time() - start_time
    logger.info(
        "Response: %s %s -> %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )

    # Add timing header
    response.headers["X-Process-Time"] = f"{process_time:.3f}"

    return response


def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Convert FastAPI HTTP exceptions to flat RFC 7807 responses.

    Returns:
        Problem Details JSON response.
    """
    if isinstance(exc.detail, dict):
        detail_data = cast("dict[str, Any]", exc.detail)
        detail = str(detail_data.get("detail", str(exc.detail)))
        error_type = str(detail_data.get("type", "/errors/http-error"))
        title = str(detail_data.get("title", "HTTP Error"))
    else:
        detail = str(exc.detail)
        error_type = "/errors/http-error"
        title = "HTTP Error"

    return _create_error_response(
        error_type,
        title,
        exc.status_code,
        detail,
        str(request.url),
    )


def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Convert FastAPI request validation failures to RFC 7807 responses.

    Returns:
        Problem Details JSON response.
    """
    return _create_error_response(
        "/errors/validation-error",
        "Request Validation Failed",
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        _format_request_validation_detail(exc),
        str(request.url),
    )


def add_middleware(app: FastAPI) -> None:
    """Add middleware and error handlers to the FastAPI application.

    Args:
        app: FastAPI application instance.
    """
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(request_validation_exception_handler)
    app.middleware("http")(error_handler_middleware)
    app.middleware("http")(logging_middleware)
