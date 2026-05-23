"""Focused tests for the MT5 connection management endpoint."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from mt5api import dependencies
from mt5api.constants import API_KEY_HEADER_NAME
from mt5api.main import app

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def connection_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[TestClient, dict[str, Any]], None, None]:
    """Test client with patched MT5 reconnect plumbing.

    Yields:
        Tuple of (TestClient, recorder dict capturing reconnect calls).
    """
    recorder: dict[str, Any] = {
        "configs": [],
        "old_client": None,
    }
    old_client = Mock(name="old_mt5_client")
    new_client = Mock(name="new_mt5_client")
    recorder["old_client"] = old_client
    recorder["new_client"] = new_client

    async def fake_replace(config: object) -> Mock:
        await asyncio.sleep(0)
        recorder["configs"].append(config)
        return new_client

    monkeypatch.setattr(dependencies, "_mt5_client", old_client)
    monkeypatch.setattr(
        "mt5api.routers.connection.replace_mt5_client",
        fake_replace,
    )

    app.dependency_overrides.clear()
    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None

    with TestClient(app) as test_client:
        yield test_client, recorder

    app.dependency_overrides.clear()
    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None


def test_post_connection_login_reconnects(
    connection_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """POST /connection/login swaps the singleton and returns connection info."""
    test_client, recorder = connection_client

    response = test_client.post(
        "/connection/login",
        json={
            "login": 12345,
            "password": "s3cret",
            "server": "MetaQuotes-Demo",
            "timeout": 60000,
        },
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "login": 12345,
        "server": "MetaQuotes-Demo",
        "timeout": 60000,
        "connected": True,
    }
    assert "password" not in payload
    assert "s3cret" not in response.text

    assert len(recorder["configs"]) == 1
    config = recorder["configs"][0]
    assert config.login == 12345
    assert config.server == "MetaQuotes-Demo"
    assert config.timeout == 60000
    assert config.password == "s3cret"  # noqa: S105


def test_post_connection_login_releases_market_book(
    connection_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Reconnect should release tracked market-book subscriptions first."""
    test_client, _ = connection_client
    cleanup_client = Mock(name="cleanup_client")
    app.state.active_market_book_subscriptions = {"EURUSD", "GBPUSD"}
    app.state.market_book_cleanup_client = cleanup_client

    response = test_client.post(
        "/connection/login",
        json={
            "login": 7,
            "password": "p",
            "server": "Demo",
        },
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )

    assert response.status_code == 200
    assert cleanup_client.market_book_release.call_count == 2
    cleanup_client.market_book_release.assert_any_call(symbol="EURUSD")
    cleanup_client.market_book_release.assert_any_call(symbol="GBPUSD")
    assert app.state.active_market_book_subscriptions == set()
    assert app.state.market_book_cleanup_client is None


def test_post_connection_login_requires_api_key(
    connection_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """The login endpoint must reject requests without an API key."""
    test_client, recorder = connection_client

    response = test_client.post(
        "/connection/login",
        json={
            "login": 1,
            "password": "p",
            "server": "S",
        },
    )

    assert response.status_code == 401
    assert recorder["configs"] == []


def test_post_connection_login_validates_fields(
    connection_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """The login endpoint must validate required and bounded fields."""
    test_client, recorder = connection_client

    response = test_client.post(
        "/connection/login",
        json={
            "login": 0,
            "password": "p",
            "server": "S",
        },
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )

    assert response.status_code == 422
    assert recorder["configs"] == []


def test_replace_mt5_client_swaps_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replace_mt5_client shuts the old client down and installs the new one."""

    class DummyClient:
        def __init__(self, config: object) -> None:
            self.config = config
            self.initialized = False

        def initialize_and_login_mt5(self) -> None:
            self.initialized = True

        def shutdown(self) -> None:  # pragma: no cover - exercised via old client
            self.initialized = False

    old_client = Mock(name="old_client")
    monkeypatch.setattr(dependencies, "_mt5_client", old_client)
    monkeypatch.setattr(dependencies, "Mt5DataClient", DummyClient)

    config = Mock(name="config")

    async def run() -> DummyClient:
        async with dependencies.get_mt5_client_lock():
            client = await dependencies.replace_mt5_client(config)
        assert isinstance(client, DummyClient)
        return client

    new_client = asyncio.run(run())

    assert new_client.config is config
    assert new_client.initialized is True
    old_client.shutdown.assert_called_once_with()
    assert dependencies._mt5_client is new_client  # pyright: ignore[reportPrivateUsage]


def test_replace_mt5_client_clears_singleton_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replace_mt5_client raises and leaves the singleton cleared on failure."""

    class FailingClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            message = "boom"
            raise ValueError(message)

    old_client = Mock(name="old_client")
    monkeypatch.setattr(dependencies, "_mt5_client", old_client)
    monkeypatch.setattr(dependencies, "Mt5DataClient", FailingClient)

    async def run() -> None:
        async with dependencies.get_mt5_client_lock():
            await dependencies.replace_mt5_client(Mock(name="config"))

    with pytest.raises(RuntimeError) as excinfo:
        asyncio.run(run())

    assert "Failed to initialize MT5 client" in str(excinfo.value)
    assert dependencies._mt5_client is None  # pyright: ignore[reportPrivateUsage]
    old_client.shutdown.assert_called_once_with()


def test_replace_mt5_client_initializes_when_no_previous_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replace_mt5_client should initialize cleanly when no client exists yet."""

    class DummyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            return None

    monkeypatch.setattr(dependencies, "_mt5_client", None)
    monkeypatch.setattr(dependencies, "Mt5DataClient", DummyClient)

    async def run() -> DummyClient:
        async with dependencies.get_mt5_client_lock():
            client = await dependencies.replace_mt5_client(Mock(name="config"))
        assert isinstance(client, DummyClient)
        return client

    new_client = asyncio.run(run())

    assert dependencies._mt5_client is new_client  # pyright: ignore[reportPrivateUsage]


def test_replace_mt5_client_continues_when_old_shutdown_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failing old-client shutdown should not block the new connection."""

    class DummyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            return None

    old_client = Mock(name="old_client")
    old_client.shutdown.side_effect = RuntimeError("cannot shut down")
    monkeypatch.setattr(dependencies, "_mt5_client", old_client)
    monkeypatch.setattr(dependencies, "Mt5DataClient", DummyClient)

    async def run() -> DummyClient:
        async with dependencies.get_mt5_client_lock():
            client = await dependencies.replace_mt5_client(Mock(name="config"))
        assert isinstance(client, DummyClient)
        return client

    new_client = asyncio.run(run())

    assert dependencies._mt5_client is new_client  # pyright: ignore[reportPrivateUsage]
