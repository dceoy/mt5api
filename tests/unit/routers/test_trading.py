"""Contract tests for trading operation endpoints."""

from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException

from mt5api.constants import MT5_RUNTIME_STATE_KEY
from mt5api.dependencies import initialize_mt5_runtime_state
from mt5api.models import OrderSendRequest, ResponseFormat
from mt5api.routers.trading import post_order_send
from tests.openapi_mt5_constants import assert_openapi_mt5_order_type_schema

if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.testclient import TestClient
    from pdmt5.dataframe import Mt5DataClient

    from mt5api.dependencies import Mt5RuntimeState


def _runtime_state(client: TestClient) -> Mt5RuntimeState:
    """Return the runtime state owned by the tested application.

    Returns:
        Application-scoped MT5 runtime state.
    """
    test_app = cast("FastAPI", client.app)
    return cast(
        "Mt5RuntimeState",
        getattr(test_app.state, MT5_RUNTIME_STATE_KEY),
    )


def test_post_order_check_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check returns the order-check result."""
    request_body = {
        "request": {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.085,
        }
    }
    response = client.post("/order/check", json=request_body, headers=api_headers)
    assert response.status_code == 200
    assert response.json()["data"]["retcode"] == 0
    mock_mt5_client.order_check_as_dict.assert_called_with(
        request=request_body["request"]
    )


def test_post_order_check_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check supports Parquet output."""
    response = client.post(
        "/order/check?format=parquet",
        json={
            "request": {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 0,
                "price": 1.085,
            }
        },
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    mock_mt5_client.order_check_as_dict.assert_called_once()


def test_post_order_check_rejects_invalid_payload(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check validates trade requests before calling MT5."""
    response = client.post(
        "/order/check",
        json={"request": {"action": 1, "volume": 0.1, "type": 0}},
        headers=api_headers,
    )
    assert response.status_code == 422
    mock_mt5_client.order_check_as_dict.assert_not_called()


def test_post_symbol_select_handles_enable_flag(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Symbol selection forwards the requested enable state."""
    response = client.post(
        "/symbols/EURUSD/select?enable=false",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"] == {
        "symbol": "EURUSD",
        "enable": False,
        "success": True,
    }
    mock_mt5_client.symbol_select.assert_called_with(symbol="EURUSD", enable=False)


def test_post_symbol_select_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Symbol selection supports Parquet output."""
    response = client.post(
        "/symbols/EURUSD/select?format=parquet",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")


def test_market_book_subscribe_tracks_cleanup_owner(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Successful subscriptions are recorded in the unified runtime state."""
    response = client.post(
        "/market-book/EURUSD/subscribe",
        headers=api_headers,
    )
    state = _runtime_state(client)
    assert response.status_code == 200
    assert response.json()["data"]["subscribed"] is True
    assert state.market_book_subscriptions == {"EURUSD"}
    assert state.market_book_cleanup_client is mock_mt5_client
    mock_mt5_client.market_book_add.assert_called_with(symbol="EURUSD")


def test_market_book_subscribe_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Market-book subscription supports Parquet output."""
    response = client.post(
        "/market-book/EURUSD/subscribe?format=parquet",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")


def test_market_book_subscribe_enforces_limit(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """A new subscription is rejected when the app-scoped limit is reached."""
    state = _runtime_state(client)
    state.market_book_subscriptions.add("EURUSD")
    state.max_market_book_subscriptions = 1
    response = client.post(
        "/market-book/USDJPY/subscribe",
        headers=api_headers,
    )
    assert response.status_code == 429
    assert response.json()["title"] == "Subscription Limit Exceeded"
    assert state.market_book_subscriptions == {"EURUSD"}
    mock_mt5_client.market_book_add.assert_not_called()


def test_market_book_resubscribe_at_limit_is_allowed(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """An already tracked symbol may be subscribed again at the limit."""
    state = _runtime_state(client)
    state.market_book_subscriptions.add("EURUSD")
    state.max_market_book_subscriptions = 1
    response = client.post(
        "/market-book/EURUSD/subscribe",
        headers=api_headers,
    )
    assert response.status_code == 200
    mock_mt5_client.market_book_add.assert_called_with(symbol="EURUSD")


def test_failed_market_book_subscription_is_not_tracked(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Failed MT5 subscription calls do not mutate runtime tracking."""
    mock_mt5_client.market_book_add.return_value = False
    response = client.post(
        "/market-book/EURUSD/subscribe",
        headers=api_headers,
    )
    state = _runtime_state(client)
    assert response.status_code == 200
    assert response.json()["data"]["subscribed"] is False
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None


def test_market_book_unsubscribe_clears_last_owner(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Successful removal of the final subscription clears cleanup ownership."""
    state = _runtime_state(client)
    state.market_book_subscriptions.add("EURUSD")
    state.market_book_cleanup_client = mock_mt5_client
    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None
    mock_mt5_client.market_book_release.assert_called_with(symbol="EURUSD")


def test_market_book_unsubscribe_keeps_owner_for_remaining_symbols(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Cleanup ownership remains while another subscription is active."""
    state = _runtime_state(client)
    state.market_book_subscriptions.update({"EURUSD", "USDJPY"})
    state.market_book_cleanup_client = mock_mt5_client
    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert state.market_book_subscriptions == {"USDJPY"}
    assert state.market_book_cleanup_client is mock_mt5_client


def test_failed_market_book_unsubscribe_preserves_tracking(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Failed unsubscribe calls leave tracked ownership unchanged."""
    state = _runtime_state(client)
    state.market_book_subscriptions.add("EURUSD")
    state.market_book_cleanup_client = mock_mt5_client
    mock_mt5_client.market_book_release.return_value = False
    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert state.market_book_subscriptions == {"EURUSD"}
    assert state.market_book_cleanup_client is mock_mt5_client


def test_market_book_unsubscribe_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Market-book unsubscribe supports Parquet output."""
    response = client.post(
        "/market-book/EURUSD/unsubscribe?format=parquet",
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")


def test_market_book_symbol_length_is_validated(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Oversized market-book symbols are rejected by request validation."""
    symbol = "X" * 33
    assert (
        client.post(
            f"/market-book/{symbol}/subscribe",
            headers=api_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/market-book/{symbol}/unsubscribe",
            headers=api_headers,
        ).status_code
        == 422
    )


def test_trading_openapi_uses_mt5_order_type_schema(client: TestClient) -> None:
    """OpenAPI retains the canonical MT5 order-type schema."""
    openapi = client.get("/openapi.json").json()
    order_type_schema = openapi["components"]["schemas"]["TradeRequest"]["properties"][
        "type"
    ]
    assert_openapi_mt5_order_type_schema(order_type_schema)


def test_post_order_send_disabled_by_default(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live trading must remain disabled unless explicitly enabled."""
    monkeypatch.delenv("MT5API_ENABLE_ORDER_SEND", raising=False)
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 123456}, "expected_login": 12345},
        headers=api_headers,
    )
    assert response.status_code == 403
    mock_mt5_client.order_send_as_dict.assert_not_called()


def test_post_order_send_denied_without_configured_auth(
    client: TestClient,
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit live-trade opt-in cannot bypass missing API-key configuration."""
    from mt5api import auth  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    monkeypatch.setattr(auth, "_API_KEY", None)
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 123456}, "expected_login": 12345},
    )
    assert response.status_code == 403
    mock_mt5_client.order_send_as_dict.assert_not_called()


def test_post_order_send_rejects_missing_api_key(
    client: TestClient,
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live order sends still require the shared X-API-Key header."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 123456}, "expected_login": 12345},
    )
    assert response.status_code == 401
    mock_mt5_client.order_send_as_dict.assert_not_called()


@pytest.mark.parametrize(
    ("trade_request", "expected"),
    [
        (
            {"action": 1, "symbol": "EURUSD", "volume": 0.1, "type": 0},
            {"action": 1, "symbol": "EURUSD", "volume": 0.1, "type": 0},
        ),
        (
            {"action": 5, "symbol": "EURUSD", "volume": 0.1, "type": 2, "price": 1.01},
            {"action": 5, "symbol": "EURUSD", "volume": 0.1, "type": 2, "price": 1.01},
        ),
        (
            {"action": 6, "position": 123456, "sl": 0.0},
            {"action": 6, "position": 123456, "sl": 0.0},
        ),
        (
            {"action": 7, "order": 123456, "price": 1.02},
            {"action": 7, "order": 123456, "price": 1.02},
        ),
        ({"action": 8, "order": 123456}, {"action": 8, "order": 123456}),
        (
            {"action": 10, "position": 123456, "position_by": 789012},
            {"action": 10, "position": 123456, "position_by": 789012},
        ),
    ],
)
def test_post_order_send_forwards_action_specific_fields(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
    trade_request: dict[str, object],
    expected: dict[str, object],
) -> None:
    """All six MT5 trade actions forward their exact validated fields."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    mock_mt5_client.order_send_as_dict.return_value = {
        "retcode": 10009,
        "order": 123456,
    }
    response = client.post(
        "/order/send",
        json={"request": trade_request, "expected_login": 12345},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["retcode"] == 10009
    mock_mt5_client.order_send_as_dict.assert_called_once_with(request=expected)


def test_post_order_send_preserves_broker_rejection(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTTP success must not mask MT5 trade-server rejection retcodes."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "1")
    mock_mt5_client.order_send_as_dict.return_value = {
        "retcode": 10013,
        "comment": "Invalid request",
    }
    response = client.post(
        "/order/send?format=parquet",
        json={"request": {"action": 8, "order": 123456}, "expected_login": 12345},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    assert mock_mt5_client.order_send_as_dict.call_count == 1


def test_post_order_send_rejects_invalid_trade_payload(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validation failures must never reach the live trading primitive."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 0}, "expected_login": 12345},
        headers=api_headers,
    )
    assert response.status_code == 422
    mock_mt5_client.order_send_as_dict.assert_not_called()


def test_post_order_send_normalizes_timed_expiration(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MT5 receives absolute Unix time for timed pending orders."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    mock_mt5_client.order_send_as_dict.return_value = {"retcode": 10009}
    response = client.post(
        "/order/send",
        json={
            "request": {
                "action": 5,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 2,
                "price": 1.05,
                "expiration": "2024-01-01T00:00:00Z",
            },
            "expected_login": 12345,
        },
        headers=api_headers,
    )
    assert response.status_code == 200
    assert (
        mock_mt5_client.order_send_as_dict.call_args.kwargs["request"]["expiration"]
        == 1704067200
    )


def test_post_order_send_holds_client_lock_and_uses_active_client(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Order submission runs under the client lock using the current client."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    state = _runtime_state(client)
    active_client = Mock()
    active_client.account_info_as_dict.return_value = {"login": 12345}
    observed: dict[str, bool] = {}

    def send(request: dict[str, object]) -> dict[str, object]:
        observed["locked"] = state.client_lock.locked()
        observed["request"] = bool(request)
        return {"retcode": 10009}

    active_client.order_send_as_dict.side_effect = send
    state.client = cast("Mt5DataClient", active_client)
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 123456}, "expected_login": 12345},
        headers=api_headers,
    )
    assert response.status_code == 200
    assert observed == {"locked": True, "request": True}
    mock_mt5_client.order_send_as_dict.assert_not_called()
    assert not state.client_lock.locked()


def test_post_order_send_cancellation_keeps_lock_until_send_finishes() -> None:
    """A cancelled request keeps the lock until the native send returns."""
    app = FastAPI()
    state = initialize_mt5_runtime_state(app, max_market_book_subscriptions=1)
    started = threading.Event()
    release = threading.Event()
    sdk = Mock()
    sdk.account_info_as_dict.return_value = {"login": 1}

    def send(request: dict[str, object]) -> dict[str, object]:
        started.set()
        release.wait(timeout=5)
        return {"retcode": 10009, "request": request}

    sdk.order_send_as_dict.side_effect = send
    state.client = cast("Mt5DataClient", sdk)
    request = OrderSendRequest.model_validate({
        "request": {"action": 8, "order": 1},
        "expected_login": 1,
    })

    async def scenario() -> tuple[bool, bool]:
        task = asyncio.ensure_future(
            post_order_send(
                cast("Request", SimpleNamespace(app=app)),
                ResponseFormat.JSON,
                request,
            )
        )
        await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0.05)
        locked_while_running = state.client_lock.locked()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        return locked_while_running, state.client_lock.locked()

    assert asyncio.run(scenario()) == (True, False)


def test_post_order_send_initializes_default_client_under_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """First send initializes the default client while holding the lock."""
    app = FastAPI()
    state = initialize_mt5_runtime_state(app, max_market_book_subscriptions=1)
    observed: dict[str, bool] = {}

    class LazyClient:
        def __init__(self, config: object) -> None:
            self.config = config

        def initialize_and_login_mt5(self) -> None:
            observed["init_locked"] = state.client_lock.locked()

        def account_info_as_dict(self) -> dict[str, object]:
            return {"login": 1}

        def order_send_as_dict(self, request: dict[str, object]) -> dict[str, object]:
            return {"retcode": 10009, "request": request}

    monkeypatch.setattr("mt5api.dependencies.Mt5DataClient", LazyClient)
    request = OrderSendRequest.model_validate({
        "request": {"action": 8, "order": 1},
        "expected_login": 1,
    })
    asyncio.run(
        post_order_send(
            cast("Request", SimpleNamespace(app=app)), ResponseFormat.JSON, request
        )
    )
    assert observed == {"init_locked": True}
    assert isinstance(state.client, LazyClient)


@pytest.mark.parametrize(
    ("body_extra", "account"),
    [
        ({"expected_login": 999}, {"login": 12345, "server": "Demo"}),
        (
            {"expected_login": 12345, "expected_server": "Live"},
            {"login": 12345, "server": "Demo"},
        ),
        ({"expected_login": 12345}, {"server": "Demo"}),
    ],
)
def test_post_order_send_rejects_account_mismatch(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
    body_extra: dict[str, object],
    account: dict[str, object],
) -> None:
    """A mismatched connected account fails closed before order_send."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    mock_mt5_client.account_info_as_dict.return_value = account
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 123456}, **body_extra},
        headers=api_headers,
    )
    assert response.status_code == 409
    mock_mt5_client.order_send_as_dict.assert_not_called()


def test_post_order_send_accepts_matching_server(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A matching login and server allows the send."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    mock_mt5_client.account_info_as_dict.return_value = {
        "login": 12345,
        "server": "Demo",
    }
    mock_mt5_client.order_send_as_dict.return_value = {"retcode": 10009}
    response = client.post(
        "/order/send",
        json={
            "request": {"action": 8, "order": 123456},
            "expected_login": 12345,
            "expected_server": "Demo",
        },
        headers=api_headers,
    )
    assert response.status_code == 200
    mock_mt5_client.order_send_as_dict.assert_called_once()


def test_post_order_send_requires_expected_login(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Omitting expected_login is a validation error."""
    monkeypatch.setenv("MT5API_ENABLE_ORDER_SEND", "true")
    response = client.post(
        "/order/send",
        json={"request": {"action": 8, "order": 123456}},
        headers=api_headers,
    )
    assert response.status_code == 422
    mock_mt5_client.order_send_as_dict.assert_not_called()


def test_post_order_send_interleaved_account_switch_is_rejected() -> None:
    """A: login A, B: login B, A: send(expect A) is rejected, not sent on B."""
    app = FastAPI()
    state = initialize_mt5_runtime_state(app, max_market_book_subscriptions=1)
    sdk = Mock()
    sdk.account_info_as_dict.return_value = {"login": 111}
    state.client = cast("Mt5DataClient", sdk)
    # Client B logs in afterwards, switching the process-global account.
    sdk.account_info_as_dict.return_value = {"login": 222}
    request = OrderSendRequest.model_validate({
        "request": {"action": 8, "order": 1},
        "expected_login": 111,
    })
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            post_order_send(
                cast("Request", SimpleNamespace(app=app)),
                ResponseFormat.JSON,
                request,
            )
        )
    assert excinfo.value.status_code == 409
    sdk.order_send_as_dict.assert_not_called()
    assert not state.client_lock.locked()
