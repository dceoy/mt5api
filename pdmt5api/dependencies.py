"""FastAPI dependency injection for MT5 client and format negotiation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from fastapi import Header, Query, Request

from pdmt5.dataframe import Mt5Config, Mt5DataClient

from .models import ResponseFormat

if TYPE_CHECKING:
    from collections.abc import Callable

# Type variable for return types
T = TypeVar("T")

# Global singleton instance
_mt5_client: Mt5DataClient | None = None


def get_mt5_client() -> Mt5DataClient:
    """Get or create Mt5DataClient singleton instance.

    This dependency provides a single shared MT5 client instance across all
    requests to avoid multiple terminal connections.

    Returns:
        Mt5DataClient: Singleton MT5 client instance.

    Raises:
        RuntimeError: If MT5 client cannot be initialized.
    """
    global _mt5_client  # noqa: PLW0603

    if _mt5_client is None:
        config = Mt5Config()
        _mt5_client = Mt5DataClient(config=config)
        try:
            _mt5_client.initialize_and_login_mt5()
        except Exception as e:
            _mt5_client = None
            error_message = f"Failed to initialize MT5 client: {e!s}"
            raise RuntimeError(error_message) from e

    return _mt5_client


def shutdown_mt5_client() -> None:
    """Shutdown and cleanup MT5 client singleton.

    This should be called during application shutdown to properly
    close the MT5 connection.
    """
    global _mt5_client  # noqa: PLW0603

    if _mt5_client is not None:
        _mt5_client.shutdown()
        _mt5_client = None


async def run_in_threadpool(
    func: Callable[..., T],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> T:
    """Run synchronous MT5 function in thread pool.

    MT5 API calls are synchronous and blocking. This wrapper runs them
    in a thread pool to avoid blocking the async event loop.

    Args:
        func: Synchronous function to run.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The function's return value.
    """
    return await asyncio.to_thread(func, *args, **kwargs)


def get_response_format(
    accept: Annotated[str | None, Header()] = None,
    format_param: Annotated[ResponseFormat | None, Query(alias="format")] = None,
) -> ResponseFormat:
    """Determine response format from Accept header or query parameter.

    Priority:
    1. Query parameter (?format=json or ?format=parquet)
    2. Accept header (application/json or application/parquet)
    3. Default to JSON

    Args:
        accept: Accept header from request.
        format_param: Format query parameter.

    Returns:
        ResponseFormat: Negotiated response format.
    """
    # Query parameter takes priority
    if format_param is not None:
        return format_param

    # Check Accept header
    if accept:
        accept_lower = accept.lower()
        if "application/parquet" in accept_lower:
            return ResponseFormat.PARQUET
        if "application/json" in accept_lower:
            return ResponseFormat.JSON

    # Default to JSON
    return ResponseFormat.JSON


def get_request_info(request: Request) -> dict[str, Any]:
    """Extract request information for logging.

    Args:
        request: FastAPI request object.

    Returns:
        Dictionary with request details.
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
