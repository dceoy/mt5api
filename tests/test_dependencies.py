"""Tests for API dependency utilities."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI
from starlette.requests import Request

from mt5api import dependencies


def _request(app: FastAPI) -> Request:
    """Build a minimal request bound to ``app``.

    Returns:
        Starlette request suitable for dependency tests.
    """
    scope: dict[str, Any] = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/health",
        "headers": [(b"user-agent", b"pytest")],
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
        "server": ("testserver", 80),
        "root_path": "",
        "query_string": b"",
    }
    return Request(scope)


def test_get_request_info_extracts_request_data() -> None:
    """Test request info extraction."""
    info = dependencies.get_request_info(_request(FastAPI()))
    assert info == {
        "method": "GET",
        "url": "http://testserver/health",
        "client": "127.0.0.1",
        "user_agent": "pytest",
    }


def test_runtime_state_is_application_scoped() -> None:
    """Runtime state and reconnect lock are owned by one application."""
    app = FastAPI()
    request = _request(app)
    state = dependencies.get_mt5_runtime_state(request)
    assert dependencies.get_mt5_runtime_state(request) is state
    assert dependencies.get_mt5_client_lock(request) is state.client_lock


def test_initialize_runtime_state_accepts_explicit_limit() -> None:
    """Explicit subscription limits are retained in application state."""
    state = dependencies.initialize_mt5_runtime_state(
        FastAPI(), max_market_book_subscriptions=7
    )
    assert state.max_market_book_subscriptions == 7


def test_get_mt5_client_initializes_and_reuses_state_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MT5 client initialization is lazy and cached per application."""

    class DummyClient:
        def __init__(self, config: str) -> None:
            self.config = config
            self.initialized = False

        def initialize_and_login_mt5(self) -> None:
            self.initialized = True

        def shutdown(self) -> None:
            self.initialized = False

    monkeypatch.setattr(dependencies, "Mt5Config", lambda: "config")
    monkeypatch.setattr(dependencies, "Mt5DataClient", DummyClient)
    request = _request(FastAPI())

    client = dependencies.get_mt5_client(request)
    assert isinstance(client, DummyClient)
    assert client.initialized is True
    assert dependencies.get_mt5_client(request) is client


def test_get_mt5_client_raises_runtime_error_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failed lazy initialization leaves no cached client."""

    class FailingClient:
        def __init__(self, config: str) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            raise ValueError("boom")

    monkeypatch.setattr(dependencies, "Mt5Config", lambda: "config")
    monkeypatch.setattr(dependencies, "Mt5DataClient", FailingClient)
    request = _request(FastAPI())

    with pytest.raises(RuntimeError, match="Failed to initialize MT5 client"):
        dependencies.get_mt5_client(request)
    assert dependencies.get_mt5_runtime_state(request).client is None


def test_shutdown_mt5_client_clears_state() -> None:
    """Shutdown clears and closes the application client."""
    client = pytest.MonkeyPatch.context  # keep a concrete non-Any symbol for typing
    del client

    class DummyClient:
        shutdown_called = False

        def shutdown(self) -> None:
            self.shutdown_called = True

    dummy = DummyClient()
    state = dependencies.Mt5RuntimeState(client=dummy)  # type: ignore[arg-type]
    dependencies.shutdown_mt5_client(state)
    assert state.client is None
    assert dummy.shutdown_called is True
    dependencies.shutdown_mt5_client(state)


def test_replace_mt5_client_preserves_old_client_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reconnect swaps only after successful initialization."""

    class DummyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            return None

    old_client = object()
    state = dependencies.Mt5RuntimeState(client=old_client)  # type: ignore[arg-type]
    monkeypatch.setattr(dependencies, "Mt5DataClient", DummyClient)
    config = object()
    new_client = asyncio.run(
        dependencies.replace_mt5_client(state, config)  # type: ignore[arg-type]
    )
    assert state.client is new_client
    assert new_client.config is config

    class FailingClient(DummyClient):
        def initialize_and_login_mt5(self) -> None:
            raise ValueError("secret upstream error")

    state.client = old_client  # type: ignore[assignment]
    monkeypatch.setattr(dependencies, "Mt5DataClient", FailingClient)
    with pytest.raises(RuntimeError, match="^Failed to initialize MT5 client$"):
        asyncio.run(
            dependencies.replace_mt5_client(state, config)  # type: ignore[arg-type]
        )
    assert state.client is old_client


def test_release_market_book_subscriptions_cleans_all_state(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Subscription cleanup continues after failures and clears ownership."""

    class CleanupClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def market_book_release(self, *, symbol: str) -> None:
            self.calls.append(symbol)
            if symbol == "EURUSD":
                raise RuntimeError("boom")

    cleanup = CleanupClient()
    state = dependencies.Mt5RuntimeState(
        market_book_subscriptions={"EURUSD", "GBPUSD"},
        market_book_cleanup_client=cleanup,  # type: ignore[arg-type]
    )
    with caplog.at_level("ERROR"):
        asyncio.run(dependencies.release_market_book_subscriptions(state))
    assert set(cleanup.calls) == {"EURUSD", "GBPUSD"}
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_handles_missing_or_empty_client() -> None:
    """Missing cleanup ownership is cleared deterministically."""
    state = dependencies.Mt5RuntimeState(market_book_subscriptions={"EURUSD"})
    asyncio.run(dependencies.release_market_book_subscriptions(state))
    assert state.market_book_subscriptions == set()

    state.market_book_cleanup_client = object()  # type: ignore[assignment]
    asyncio.run(dependencies.release_market_book_subscriptions(state))
    assert state.market_book_cleanup_client is None


def test_run_in_threadpool_returns_result() -> None:
    """Threadpool helper forwards positional and keyword arguments."""
    result = asyncio.run(dependencies.run_in_threadpool(lambda a, b: a + b, 2, b=3))
    assert result == 5
