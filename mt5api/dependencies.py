"""FastAPI dependency injection for MT5 client and format negotiation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from fastapi import Header, Query, Request
from pdmt5.dataframe import Mt5Config, Mt5DataClient

from .config import get_configured_max_market_book_subscriptions
from .constants import MT5_RUNTIME_STATE_KEY
from .models import ResponseFormat

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(slots=True)
class Mt5RuntimeState:
    """Application-scoped owner for MT5 connection and subscription state."""

    client: Mt5DataClient | None = None
    client_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    market_book_subscriptions: set[str] = field(default_factory=set)
    market_book_cleanup_client: Mt5DataClient | None = None
    max_market_book_subscriptions: int = 0


def initialize_mt5_runtime_state(
    app: FastAPI,
    *,
    max_market_book_subscriptions: int | None = None,
) -> Mt5RuntimeState:
    """Create and install the application-scoped MT5 runtime state.

    Args:
        app: FastAPI application that owns the state.
        max_market_book_subscriptions: Optional explicit subscription limit.

    Returns:
        The newly installed runtime state.
    """
    state = Mt5RuntimeState(
        max_market_book_subscriptions=(
            get_configured_max_market_book_subscriptions()
            if max_market_book_subscriptions is None
            else max_market_book_subscriptions
        )
    )
    setattr(app.state, MT5_RUNTIME_STATE_KEY, state)
    return state


def get_mt5_runtime_state(request: Request) -> Mt5RuntimeState:
    """Return the request application's MT5 runtime state.

    A state object is installed lazily for direct ASGI/test usage that bypasses
    the application's lifespan hook; normal application startup installs it
    explicitly.
    """
    state = getattr(request.app.state, MT5_RUNTIME_STATE_KEY, None)
    if isinstance(state, Mt5RuntimeState):
        return state
    return initialize_mt5_runtime_state(request.app)


def get_mt5_client_lock(request: Request) -> asyncio.Lock:
    """Return the application-scoped lock guarding MT5 client replacement."""
    return get_mt5_runtime_state(request).client_lock


def get_mt5_client(request: Request) -> Mt5DataClient:
    """Get or create the application-scoped MT5 client instance.

    Args:
        request: Request whose application owns the MT5 runtime state.

    Returns:
        Shared initialized MT5 data client.

    Raises:
        RuntimeError: If MT5 client initialization fails.
    """
    state = get_mt5_runtime_state(request)
    if state.client is None:
        client = Mt5DataClient(config=Mt5Config())
        try:
            client.initialize_and_login_mt5()
        except Exception as exc:
            error_message = f"Failed to initialize MT5 client: {exc!s}"
            raise RuntimeError(error_message) from exc
        state.client = client
    return state.client


def shutdown_mt5_client(state: Mt5RuntimeState) -> None:
    """Shutdown and clear the application-scoped MT5 client."""
    client = state.client
    if client is None:
        return
    state.client = None
    client.shutdown()


async def replace_mt5_client(
    state: Mt5RuntimeState,
    config: Mt5Config,
) -> Mt5DataClient:
    """Replace the application's MT5 client with a newly initialized connection.

    The replacement is initialized before ``state.client`` is changed. The
    MetaTrader5 Python module has process-global connection state, so the
    previous wrapper must not be shut down after a successful reconnect: doing
    so would close the newly opened process-global connection. Callers must
    hold ``state.client_lock`` while replacing the client and clearing
    subscription state.

    Args:
        state: Application-scoped runtime state to update.
        config: Configuration for the new MT5 connection.

    Returns:
        The newly initialized MT5 data client.

    Raises:
        RuntimeError: If the new client cannot be constructed or initialized.
    """
    try:
        new_client = Mt5DataClient(config=config)
        await asyncio.to_thread(new_client.initialize_and_login_mt5)
    except Exception as exc:
        logger.exception("Failed to initialize MT5 client")
        error_message = "Failed to initialize MT5 client"
        raise RuntimeError(error_message) from exc

    state.client = new_client
    return new_client


async def release_market_book_subscriptions(state: Mt5RuntimeState) -> None:
    """Release and clear all market-book subscriptions owned by ``state``."""
    subscriptions = state.market_book_subscriptions
    if not subscriptions:
        state.market_book_cleanup_client = None
        return

    cleanup_client = state.market_book_cleanup_client
    if cleanup_client is None:
        logger.warning("Active market-book subscriptions found without cleanup client")
        subscriptions.clear()
        return

    def release_subscriptions() -> None:
        for symbol in tuple(subscriptions):
            try:
                cleanup_client.market_book_release(symbol=symbol)
            except Exception:
                logger.exception("Failed to release market book for %s", symbol)

    await asyncio.to_thread(release_subscriptions)
    subscriptions.clear()
    state.market_book_cleanup_client = None


async def run_in_threadpool(
    func: Callable[..., T],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> T:
    """Run a synchronous MT5 function without blocking the event loop."""
    return await asyncio.to_thread(func, *args, **kwargs)


def get_response_format(
    accept: Annotated[str | None, Header()] = None,
    format_param: Annotated[ResponseFormat | None, Query(alias="format")] = None,
) -> ResponseFormat:
    """Determine response format from query parameter or Accept header."""
    if format_param is not None:
        return format_param

    if accept:
        accept_lower = accept.lower()
        if "application/parquet" in accept_lower:
            return ResponseFormat.PARQUET
        if "application/json" in accept_lower:
            return ResponseFormat.JSON

    return ResponseFormat.JSON


def get_request_info(request: Request) -> dict[str, Any]:
    """Extract request information for logging."""
    return {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
