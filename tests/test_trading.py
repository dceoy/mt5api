"""Contract tests for trading operation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from fastapi.testclient import TestClient

from mt5api.constants import MT5_RUNTIME_STATE_KEY
from mt5api.dependencies import Mt5RuntimeState
from tests.openapi_mt5_constants import assert_openapi_mt5_order_type_schema

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi import FastAPI


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
    assert_openapi_mt5_order_type_schema(client.get("/openapi.json").json())
