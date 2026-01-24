"""Tests for API dependency utilities."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request


def test_get_request_info_extracts_request_data() -> None:
    """Test request info extraction."""
    from pdmt5.api.dependencies import get_request_info  # noqa: PLC0415

    scope: dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/health",
        "headers": [(b"user-agent", b"pytest")],
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
        "server": ("testserver", 80),
        "root_path": "",
        "query_string": b"",
    }

    info = get_request_info(Request(scope))

    assert info == {
        "method": "GET",
        "url": "http://testserver/api/v1/health",
        "client": "127.0.0.1",
        "user_agent": "pytest",
    }


def test_get_mt5_client_initializes_and_returns_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MT5 client initialization success path."""
    from pdmt5.api import dependencies  # noqa: PLC0415

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
    monkeypatch.setattr(dependencies, "_mt5_client", None)

    client = dependencies.get_mt5_client()

    assert isinstance(client, DummyClient)


def test_get_mt5_client_returns_existing_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test returning existing MT5 client without reinitialization."""
    from pdmt5.api import dependencies  # noqa: PLC0415

    existing_client = object()
    monkeypatch.setattr(dependencies, "_mt5_client", existing_client)

    client = dependencies.get_mt5_client()

    assert client is existing_client


def test_get_mt5_client_raises_runtime_error_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MT5 client initialization failure path."""
    from pdmt5.api import dependencies  # noqa: PLC0415

    class FailingClient:
        def __init__(self, config: str) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            error_message = "boom"
            raise ValueError(error_message)

    monkeypatch.setattr(dependencies, "Mt5Config", lambda: "config")
    monkeypatch.setattr(dependencies, "Mt5DataClient", FailingClient)
    monkeypatch.setattr(dependencies, "_mt5_client", None)

    with pytest.raises(RuntimeError) as excinfo:
        dependencies.get_mt5_client()

    assert "Failed to initialize MT5 client" in str(excinfo.value)

    class DummyClient:
        def __init__(self, config: str) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            return None

    monkeypatch.setattr(dependencies, "Mt5DataClient", DummyClient)

    client = dependencies.get_mt5_client()

    assert isinstance(client, DummyClient)


def test_shutdown_mt5_client_resets_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test shutdown clears singleton and calls shutdown."""
    from pdmt5.api import dependencies  # noqa: PLC0415

    class DummyClient:
        def __init__(self) -> None:
            self.shutdown_called = False

        def shutdown(self) -> None:
            self.shutdown_called = True

    client = DummyClient()
    monkeypatch.setattr(dependencies, "_mt5_client", client)

    dependencies.shutdown_mt5_client()

    class NewClient:
        def __init__(self, config: str) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            return None

    monkeypatch.setattr(dependencies, "Mt5Config", lambda: "config")
    monkeypatch.setattr(dependencies, "Mt5DataClient", NewClient)

    new_client = dependencies.get_mt5_client()

    assert (client.shutdown_called, new_client is client) == (True, False)


def test_shutdown_mt5_client_noop_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test shutdown is a no-op when no singleton is set."""
    from pdmt5.api import dependencies  # noqa: PLC0415

    monkeypatch.setattr(dependencies, "_mt5_client", None)

    result = dependencies.shutdown_mt5_client()

    assert result is None
