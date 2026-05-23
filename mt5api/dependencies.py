"""FastAPI dependency injection for MT5 client and format negotiation."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from fastapi import Header, Query, Request
from pdmt5.dataframe import Mt5Config, Mt5DataClient

from .constants import (
    ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
    MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY,
)
from .models import ResponseFormat

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Type variable for return types
T = TypeVar("T")

# Global singleton instance
_mt5_client: Mt5DataClient | None = None

# Serializes singleton replacement across concurrent reconnect requests.
_mt5_client_lock = asyncio.Lock()


def get_mt5_client_lock() -> asyncio.Lock:
    """Return the lock guarding MT5 client singleton replacement."""
    return _mt5_client_lock


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


async def replace_mt5_client(config: Mt5Config) -> Mt5DataClient:
    """Swap the MT5 client singleton with a new connection.

    Shuts down the previous client (if any) and creates a fresh
    ``Mt5DataClient`` using ``config``. Callers MUST hold
    ``get_mt5_client_lock`` for the duration of the swap so concurrent
    reconnect requests do not race.

    Args:
        config: Configuration for the new MT5 connection.

    Returns:
        The newly initialized MT5 data client.

    Raises:
        RuntimeError: If the new MT5 client cannot be initialized.
    """
    global _mt5_client  # noqa: PLW0603

    old_client = _mt5_client
    _mt5_client = None
    if old_client is not None:
        try:
            await asyncio.to_thread(old_client.shutdown)
        except Exception:
            logger.exception("Failed to shutdown previous MT5 client")

    new_client = Mt5DataClient(config=config)
    try:
        await asyncio.to_thread(new_client.initialize_and_login_mt5)
    except Exception as e:
        error_message = f"Failed to initialize MT5 client: {e!s}"
        raise RuntimeError(error_message) from e

    _mt5_client = new_client
    return new_client


async def release_market_book_subscriptions(app: FastAPI) -> None:
    """Release tracked market-book subscriptions on the application.

    Iterates the application's tracked subscription set, calls
    ``market_book_release`` for each symbol using the cleanup client, then
    clears the tracking state. Individual release failures are logged and do
    not stop processing.

    Args:
        app: FastAPI application whose state holds the subscription set.
    """
    subscriptions = getattr(
        app.state,
        ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
        None,
    )
    if not isinstance(subscriptions, set) or not subscriptions:
        return

    mt5_client = getattr(app.state, MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
    if mt5_client is None:
        logger.warning("Active market-book subscriptions found without cleanup client")
        subscriptions.clear()
        setattr(app.state, MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
        return

    for symbol in tuple(sorted(subscriptions)):
        try:
            await asyncio.to_thread(mt5_client.market_book_release, symbol=symbol)
        except Exception:
            logger.exception("Failed to release market book for %s", symbol)

    subscriptions.clear()
    setattr(app.state, MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)


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
