"""Focused tests for the MT5 connection management endpoint."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient

from mt5api import dependencies
from mt5api.constants import API_KEY_HEADER_NAME, MT5_RUNTIME_STATE_KEY
from mt5api.main import app

if TYPE_CHECKING:
    from collections.abc import Generator

    import httpx2
    from pytest_mock import MockerFixture


def _runtime_state() -> dependencies.Mt5RuntimeState:
    """Return the lifespan-owned application runtime state.

    Returns:
        Current application-scoped MT5 runtime state.
    """
    return cast(
        "dependencies.Mt5RuntimeState",
        getattr(app.state, MT5_RUNTIME_STATE_KEY),
    )


@pytest.fixture
def connection_client(
    mocker: MockerFixture,
) -> Generator[tuple[TestClient, dict[str, Any]], None, None]:
    """Create a test client with patched reconnect initialization.

    Yields:
        Test client and a recorder containing replacement configs.
    """
    recorder: dict[str, Any] = {"configs": []}
    new_client = mocker.Mock(name="new_mt5_client")
    recorder["new_client"] = new_client

    def fake_replace(
        state: dependencies.Mt5RuntimeState,
        config: object,
    ) -> object:
        recorder["configs"].append(config)
        state.client = new_client
        return new_client

    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=fake_replace,
    )
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client, recorder
    app.dependency_overrides.clear()


def _login(
    test_client: TestClient,
    *,
    login: int = 12345,
    password: str | None = None,
    server: str = "MetaQuotes-Demo",
    timeout: int | None = None,
) -> httpx2.Response:
    """Submit a valid authenticated login request.

    Returns:
        HTTP response from the login endpoint.
    """
    request_password = "s3cret" if password is None else password
    request_body: dict[str, object] = {
        "login": login,
        "password": request_password,
        "server": server,
    }
    if timeout is not None:
        request_body["timeout"] = timeout
    return test_client.post(
        "/connection/login",
        json=request_body,
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )


def test_post_connection_login_reconnects(
    connection_client: tuple[TestClient, dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """POST /connection/login installs the replacement and returns metadata."""
    test_client, recorder = connection_client
    with caplog.at_level("INFO"):
        response = _login(test_client, timeout=60000)
    assert response.status_code == 200
    assert response.json() == {
        "login": 12345,
        "server": "MetaQuotes-Demo",
        "timeout": 60000,
        "connected": True,
    }
    config = recorder["configs"][0]
    assert config.login == 12345
    assert config.server == "MetaQuotes-Demo"
    assert config.password.get_secret_value() == "s3cret"
    assert _runtime_state().client is recorder["new_client"]
    assert all("s3cret" not in record.getMessage() for record in caplog.records)


def test_post_connection_login_releases_market_book_after_success(
    connection_client: tuple[TestClient, dict[str, Any]],
    mocker: MockerFixture,
) -> None:
    """Successful reconnect releases subscriptions after replacement."""
    test_client, _ = connection_client
    cleanup_client = mocker.Mock(name="cleanup_client")
    state = _runtime_state()
    state.market_book_subscriptions.update({"EURUSD", "GBPUSD"})
    state.market_book_cleanup_client = cleanup_client
    response = _login(test_client, login=7, password="p", server="Demo")
    assert response.status_code == 200
    cleanup_client.market_book_release.assert_any_call(symbol="EURUSD")
    cleanup_client.market_book_release.assert_any_call(symbol="GBPUSD")
    assert cleanup_client.market_book_release.call_count == 2
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None


def test_post_connection_login_preserves_subscriptions_on_failure(
    connection_client: tuple[TestClient, dict[str, Any]],
    mocker: MockerFixture,
) -> None:
    """Failed replacement does not clear pre-existing subscription ownership."""
    test_client, recorder = connection_client
    cleanup_client = mocker.Mock(name="cleanup_client")
    state = _runtime_state()
    state.market_book_subscriptions.add("EURUSD")
    state.market_book_cleanup_client = cleanup_client

    def fail_replace(
        runtime_state: dependencies.Mt5RuntimeState,
        config: object,
    ) -> None:
        del runtime_state
        recorder["configs"].append(config)
        error_message = "connection unavailable"
        raise RuntimeError(error_message)

    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=fail_replace,
    )
    response = _login(test_client, login=7, password="p", server="Demo")
    assert response.status_code == 503
    cleanup_client.market_book_release.assert_not_called()
    assert state.market_book_subscriptions == {"EURUSD"}
    assert state.market_book_cleanup_client is cleanup_client


def test_post_connection_login_requires_api_key(
    connection_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """The login endpoint rejects unauthenticated requests."""
    test_client, recorder = connection_client
    response = test_client.post(
        "/connection/login",
        json={"login": 1, "password": "p", "server": "S"},
    )
    assert response.status_code == 401
    assert recorder["configs"] == []


@pytest.mark.parametrize(
    "body",
    [
        {"password": "p", "server": "S"},
        {"login": 1, "server": "S"},
        {"login": 1, "password": "p"},
        {"login": 0, "password": "p", "server": "S"},
        {"login": 1, "password": "", "server": "S"},
        {"login": 1, "password": "p", "server": ""},
        {"login": 1, "password": "p", "server": "S", "timeout": 0},
        {"login": 1, "password": "p", "server": "S", "extra": "nope"},
    ],
)
def test_post_connection_login_validates_fields(
    connection_client: tuple[TestClient, dict[str, Any]],
    body: dict[str, Any],
) -> None:
    """The login endpoint rejects malformed payloads before reconnecting."""
    test_client, recorder = connection_client
    response = test_client.post(
        "/connection/login",
        json=body,
        headers={API_KEY_HEADER_NAME: "test-api-key-12345"},
    )
    assert response.status_code == 422
    assert recorder["configs"] == []


def test_post_connection_login_failure_does_not_leak_password(
    mocker: MockerFixture,
) -> None:
    """Upstream exceptions containing credentials are not reflected to clients."""
    password = "very-secret-pa55word-XYZ"  # noqa: S105

    class LeakyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            message = f"upstream MT5 error referencing config {self.config!r}"
            raise ValueError(message)

    mocker.patch.object(dependencies, "Mt5DataClient", LeakyClient)
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        response = _login(test_client, password=password)
    assert response.status_code == 503
    assert password not in response.text
    assert "upstream MT5 error" not in response.text


def test_post_connection_login_serializes_concurrent_reconnects(
    mocker: MockerFixture,
) -> None:
    """Application-scoped lock serializes concurrent reconnect requests."""
    active_count = 0
    max_active_count = 0
    login_values: list[int] = []

    async def fake_replace(
        state: dependencies.Mt5RuntimeState,
        config: object,
    ) -> None:
        nonlocal active_count, max_active_count
        del state
        active_count += 1
        max_active_count = max(max_active_count, active_count)
        login_values.append(cast("Any", config).login)
        await asyncio.sleep(0.01)
        active_count -= 1

    mocker.patch(
        "mt5api.routers.connection.replace_mt5_client",
        side_effect=fake_replace,
    )
    app.dependency_overrides.clear()
    dependencies.initialize_mt5_runtime_state(app, max_market_book_subscriptions=100)

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
