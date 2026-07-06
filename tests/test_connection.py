"""Focused tests for the MT5 connection management endpoint."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient

from mt5api import dependencies
from mt5api.constants import API_KEY_HEADER_NAME
from mt5api.main import app

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest_mock import MockerFixture


@pytest.fixture
def connection_client(
    mocker: MockerFixture,
) -> Generator[tuple[TestClient, dict[str, Any]], None, None]:
    """Test client with patched MT5 reconnect plumbing.

    Yields:
        Tuple of (TestClient, recorder dict capturing reconnect calls).
    """
    recorder: dict[str, Any] = {
        "configs": [],
        "old_client": None,
    }
    old_client = mocker.Mock(name="old_mt5_client")
    new_client = mocker.Mock(name="new_mt5_client")
    recorder["old_client"] = old_client
    recorder["new_client"] = new_client

    async def fake_replace(config: object) -> object:
        await asyncio.sleep(0)
        recorder["configs"].append(config)
        return new_client

    mocker.patch.object(dependencies, "_mt5_client", old_client)
    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=fake_replace,
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
    caplog: pytest.LogCaptureFixture,
) -> None:
    """POST /connection/login swaps the singleton and returns connection info."""
    test_client, recorder = connection_client

    with caplog.at_level("INFO"):
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
    assert all("s3cret" not in record.getMessage() for record in caplog.records)


def test_post_connection_login_releases_market_book_after_reconnect(
    connection_client: tuple[TestClient, dict[str, Any]],
    mocker: MockerFixture,
) -> None:
    """Reconnect should release tracked market-book subscriptions after success."""
    test_client, _ = connection_client
    cleanup_client = mocker.Mock(name="cleanup_client")
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


def test_post_connection_login_preserves_market_book_on_reconnect_failure(
    connection_client: tuple[TestClient, dict[str, Any]],
    mocker: MockerFixture,
) -> None:
    """Reconnect failure should not drop tracked market-book subscriptions."""
    test_client, recorder = connection_client
    cleanup_client = mocker.Mock(name="cleanup_client")
    app.state.active_market_book_subscriptions = {"EURUSD"}
    app.state.market_book_cleanup_client = cleanup_client

    async def fail_replace(config: object) -> None:
        await asyncio.sleep(0)
        recorder["configs"].append(config)
        error_message = "connection unavailable"
        raise RuntimeError(error_message)

    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=fail_replace,
    )

    response = test_client.post(
        "/connection/login",
        json={
            "login": 7,
            "password": "p",
            "server": "Demo",
        },
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )

    assert response.status_code == 503
    cleanup_client.market_book_release.assert_not_called()
    assert app.state.active_market_book_subscriptions == {"EURUSD"}
    assert app.state.market_book_cleanup_client is cleanup_client


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


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            {"password": "p", "server": "S"},
            id="missing-login",
        ),
        pytest.param(
            {"login": 1, "server": "S"},
            id="missing-password",
        ),
        pytest.param(
            {"login": 1, "password": "p"},
            id="missing-server",
        ),
        pytest.param(
            {"login": 0, "password": "p", "server": "S"},
            id="login-not-positive",
        ),
        pytest.param(
            {"login": 1, "password": "", "server": "S"},
            id="password-empty",
        ),
        pytest.param(
            {"login": 1, "password": "x" * 129, "server": "S"},
            id="password-too-long",
        ),
        pytest.param(
            {"login": 1, "password": "p", "server": ""},
            id="server-empty",
        ),
        pytest.param(
            {"login": 1, "password": "p", "server": "x" * 129},
            id="server-too-long",
        ),
        pytest.param(
            {"login": 1, "password": "p", "server": "S", "timeout": 0},
            id="timeout-not-positive",
        ),
        pytest.param(
            {"login": 1, "password": "p", "server": "S", "extra": "nope"},
            id="extra-field-forbidden",
        ),
    ],
)
def test_post_connection_login_validates_fields(
    connection_client: tuple[TestClient, dict[str, Any]],
    body: dict[str, Any],
) -> None:
    """The login endpoint must reject malformed or out-of-bounds payloads."""
    test_client, recorder = connection_client

    response = test_client.post(
        "/connection/login",
        json=body,
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )

    assert response.status_code == 422
    assert recorder["configs"] == []


def test_post_connection_login_does_not_leak_password_on_failure(
    mocker: MockerFixture,
) -> None:
    """A reconnect failure must never reflect the password in the HTTP body.

    Simulates an upstream MT5 exception that quotes the password (as
    ``pdmt5``/MetaTrader5 can do via ``Mt5Config.__repr__``) and asserts the
    HTTP response body contains neither the password nor the underlying
    exception text. Server-side logs may still record diagnostics.
    """
    password = "very-secret-pa55word-XYZ"  # noqa: S105

    class LeakyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            message = f"upstream MT5 error referencing config {self.config!r}"
            raise ValueError(message)

    mocker.patch.object(dependencies, "_mt5_client", mocker.Mock(name="old"))
    mocker.patch.object(dependencies, "Mt5DataClient", LeakyClient)
    app.dependency_overrides.clear()
    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None

    with TestClient(app) as test_client:
        response = test_client.post(
            "/connection/login",
            json={
                "login": 12345,
                "password": password,
                "server": "MetaQuotes-Demo",
            },
            headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
        )

    assert response.status_code == 503
    assert password not in response.text
    assert "upstream MT5 error" not in response.text


def test_post_connection_login_runtime_error_returns_problem_details(
    mocker: MockerFixture,
) -> None:
    """Runtime reconnect failures should return RFC 7807 problem details."""
    error_message = "connection unavailable"

    mocker.patch.object(dependencies, "_mt5_client", mocker.Mock(name="old"))
    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=RuntimeError(error_message),
    )
    app.dependency_overrides.clear()
    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None

    with TestClient(app) as test_client:
        response = test_client.post(
            "/connection/login",
            json={
                "login": 12345,
                "password": "s3cret",
                "server": "MetaQuotes-Demo",
            },
            headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "type": "/errors/runtime-error",
        "title": "Runtime Error",
        "status": 503,
        "detail": "connection unavailable",
        "instance": "http://testserver/connection/login",
    }


def test_post_connection_login_serializes_concurrent_reconnects(
    mocker: MockerFixture,
) -> None:
    """Concurrent login requests should enter reconnect one at a time."""
    active_count = 0
    max_active_count = 0
    login_values: list[int] = []

    async def fake_replace(config: object) -> None:
        nonlocal active_count, max_active_count
        active_count += 1
        max_active_count = max(max_active_count, active_count)
        login_values.append(cast("Any", config).login)
        await asyncio.sleep(0.01)
        active_count -= 1

    mocker.patch.object(dependencies, "_mt5_client", mocker.Mock(name="old"))
    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=fake_replace,
    )
    app.dependency_overrides.clear()
    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None

    async def post_login(test_client: httpx.AsyncClient, login: int) -> httpx.Response:
        return await test_client.post(
            "/connection/login",
            json={
                "login": login,
                "password": "s3cret",
                "server": "MetaQuotes-Demo",
            },
            headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
        )

    async def run_requests() -> list[httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as test_client:
            return list(
                await asyncio.gather(
                    post_login(test_client, 12345),
                    post_login(test_client, 23456),
                )
            )

    responses = asyncio.run(run_requests())

    assert [response.status_code for response in responses] == [200, 200]
    assert max_active_count == 1
    assert sorted(login_values) == [12345, 23456]


def test_replace_mt5_client_swaps_singleton(
    mocker: MockerFixture,
) -> None:
    """replace_mt5_client installs the new client without shutting down MT5."""

    class DummyClient:
        def __init__(self, config: object) -> None:
            self.config = config
            self.initialized = False

        def initialize_and_login_mt5(self) -> None:
            self.initialized = True

        def shutdown(self) -> None:  # pragma: no cover - exercised via old client
            self.initialized = False

    old_client = mocker.Mock(name="old_client")
    mocker.patch.object(dependencies, "_mt5_client", old_client)
    mocker.patch.object(dependencies, "Mt5DataClient", DummyClient)

    config = mocker.Mock(name="config")

    async def run() -> DummyClient:
        async with dependencies.get_mt5_client_lock():
            client = await dependencies.replace_mt5_client(config)
        assert isinstance(client, DummyClient)
        return client

    new_client = asyncio.run(run())

    assert new_client.config is config
    assert new_client.initialized is True
    old_client.shutdown.assert_not_called()
    assert dependencies._mt5_client is new_client  # pyright: ignore[reportPrivateUsage]


def test_replace_mt5_client_preserves_old_client_on_failure(
    mocker: MockerFixture,
) -> None:
    """A failed init must keep the previously installed client in place."""
    password = "leaked-password-AAA"  # noqa: S105

    class FailingClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            # Simulate an upstream exception that quotes the secret config.
            message = f"login refused for {password}"
            raise ValueError(message)

    old_client = mocker.Mock(name="old_client")
    mocker.patch.object(dependencies, "_mt5_client", old_client)
    mocker.patch.object(dependencies, "Mt5DataClient", FailingClient)

    async def run() -> None:
        async with dependencies.get_mt5_client_lock():
            await dependencies.replace_mt5_client(mocker.Mock(name="config"))

    with pytest.raises(RuntimeError) as excinfo:
        asyncio.run(run())

    # The raised message must not include the underlying exception text so
    # any credentials embedded by upstream libraries do not surface to clients.
    assert str(excinfo.value) == "Failed to initialize MT5 client"
    assert password not in str(excinfo.value)
    # Previous client is preserved and was NOT shut down.
    assert dependencies._mt5_client is old_client  # pyright: ignore[reportPrivateUsage]
    old_client.shutdown.assert_not_called()


def test_replace_mt5_client_initializes_when_no_previous_client(
    mocker: MockerFixture,
) -> None:
    """replace_mt5_client should initialize cleanly when no client exists yet."""

    class DummyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            return None

    mocker.patch.object(dependencies, "_mt5_client", None)
    mocker.patch.object(dependencies, "Mt5DataClient", DummyClient)

    async def run() -> DummyClient:
        async with dependencies.get_mt5_client_lock():
            client = await dependencies.replace_mt5_client(mocker.Mock(name="config"))
        assert isinstance(client, DummyClient)
        return client

    new_client = asyncio.run(run())

    assert dependencies._mt5_client is new_client  # pyright: ignore[reportPrivateUsage]
