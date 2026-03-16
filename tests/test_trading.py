"""Contract tests for trading operation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import call

from fastapi.testclient import TestClient

from mt5api import dependencies
from mt5api.main import app
from mt5api.routers import health

if TYPE_CHECKING:
    from unittest.mock import Mock

    import pytest
    from fastapi import FastAPI


def test_post_order_check_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check returns order check result."""
    request_body = {
        "request": {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.08500,
        },
    }
    response = client.post(
        "/order/check",
        json=request_body,
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["retcode"] == 0
    assert payload["data"]["comment"] == "Done"

    mock_mt5_client.order_check_as_dict.assert_called_with(
        request=request_body["request"],
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
                "price": 1.08500,
            }
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    mock_mt5_client.order_check_as_dict.assert_called_once()


def test_post_order_check_validates_payload(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check rejects invalid request bodies."""
    request_body = {
        "request": {
            "action": 1,
            "volume": 0.1,
            "type": 0,
            "price": 1.08500,
        },
    }
    response = client.post(
        "/order/check",
        json=request_body,
        headers=api_headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "symbol"
    mock_mt5_client.order_check_as_dict.assert_not_called()


def test_post_order_check_allows_supported_optional_mt5_fields(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check preserves whitelisted optional MT5 trade-request fields."""
    request_body = {
        "request": {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": "ORDER_TYPE_BUY",
            "price": 1.08500,
            "deviation": 10,
            "comment": "validation-check",
            "type_filling": 1,
            "position": 123456,
        },
    }
    response = client.post(
        "/order/check",
        json=request_body,
        headers=api_headers,
    )

    assert response.status_code == 200

    mock_mt5_client.order_check_as_dict.assert_called_with(
        request={
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.08500,
            "deviation": 10,
            "comment": "validation-check",
            "type_filling": 1,
            "position": 123456,
        },
    )


def test_post_order_check_rejects_unknown_trade_request_field(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check rejects unrecognized trade-request fields."""
    response = client.post(
        "/order/check",
        json={
            "request": {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 0,
                "price": 1.08500,
                "unsupported": True,
            }
        },
        headers=api_headers,
    )

    assert response.status_code == 422
    mock_mt5_client.order_check_as_dict.assert_not_called()


def test_post_order_check_rejects_invalid_optional_mt5_field_type(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/check validates the types of optional MT5 trade-request fields."""
    response = client.post(
        "/order/check",
        json={
            "request": {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 0,
                "price": 1.08500,
                "magic": [1, 2, 3],
            }
        },
        headers=api_headers,
    )

    assert response.status_code == 422
    mock_mt5_client.order_check_as_dict.assert_not_called()


def test_post_symbol_select_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /symbols/{symbol}/select returns selection result."""
    response = client.post(
        "/symbols/EURUSD/select",
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["symbol"] == "EURUSD"
    assert payload["data"]["enable"] is True
    assert payload["data"]["success"] is True

    mock_mt5_client.symbol_select.assert_called_with(
        symbol="EURUSD",
        enable=True,
    )


def test_post_symbol_select_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /symbols/{symbol}/select supports Parquet output."""
    response = client.post(
        "/symbols/EURUSD/select?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    mock_mt5_client.symbol_select.assert_called_with(
        symbol="EURUSD",
        enable=True,
    )


def test_post_symbol_select_with_disable(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /symbols/{symbol}/select supports enable=false."""
    response = client.post(
        "/symbols/EURUSD/select?enable=false",
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["data"]["enable"] is False

    mock_mt5_client.symbol_select.assert_called_with(
        symbol="EURUSD",
        enable=False,
    )


def test_post_symbol_select_returns_false_when_mt5_rejects(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /symbols/{symbol}/select exposes MT5 selection failures."""
    mock_mt5_client.symbol_select.return_value = False

    response = client.post(
        "/symbols/EURUSD/select",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["success"] is False
    mock_mt5_client.symbol_select.assert_called_with(
        symbol="EURUSD",
        enable=True,
    )


def test_post_market_book_subscribe_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /market-book/{symbol}/subscribe returns result."""
    response = client.post(
        "/market-book/EURUSD/subscribe",
        headers=api_headers,
    )

    assert response.status_code == 200
    test_app = cast("FastAPI", client.app)

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["symbol"] == "EURUSD"
    assert payload["data"]["subscribed"] is True
    assert test_app.state.active_market_book_subscriptions == {"EURUSD"}
    assert test_app.state.market_book_cleanup_client is mock_mt5_client

    mock_mt5_client.market_book_add.assert_called_with(symbol="EURUSD")


def test_post_market_book_subscribe_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /market-book/{symbol}/subscribe supports Parquet output."""
    response = client.post(
        "/market-book/EURUSD/subscribe?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    mock_mt5_client.market_book_add.assert_called_with(symbol="EURUSD")


def test_post_market_book_subscribe_validates_symbol_length(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """POST /market-book/{symbol}/subscribe rejects oversized symbols."""
    response = client.post(
        f"/market-book/{'X' * 33}/subscribe",
        headers=api_headers,
    )

    assert response.status_code == 422


def test_post_market_book_subscribe_rejects_when_subscription_limit_exceeded(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """New subscriptions should be rejected once the tracked limit is reached."""
    test_app = cast("FastAPI", client.app)
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.max_market_book_subscriptions = 1

    response = client.post(
        "/market-book/USDJPY/subscribe",
        headers=api_headers,
    )

    assert response.status_code == 429
    assert response.json()["title"] == "Subscription Limit Exceeded"
    assert test_app.state.active_market_book_subscriptions == {"EURUSD"}
    mock_mt5_client.market_book_add.assert_not_called()


def test_post_market_book_subscribe_allows_existing_symbol_at_limit(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Re-subscribing an already tracked symbol should not be rejected by the cap."""
    test_app = cast("FastAPI", client.app)
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.max_market_book_subscriptions = 1

    response = client.post(
        "/market-book/EURUSD/subscribe",
        headers=api_headers,
    )

    assert response.status_code == 200
    mock_mt5_client.market_book_add.assert_called_with(symbol="EURUSD")


def test_post_market_book_subscribe_does_not_track_failed_subscription(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Failed subscriptions should not update tracked market-book state."""
    test_app = cast("FastAPI", client.app)
    mock_mt5_client.market_book_add.return_value = False

    response = client.post(
        "/market-book/EURUSD/subscribe",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None


def test_post_market_book_unsubscribe_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /market-book/{symbol}/unsubscribe returns result."""
    test_app = cast("FastAPI", client.app)
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.market_book_cleanup_client = mock_mt5_client

    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["symbol"] == "EURUSD"
    assert payload["data"]["unsubscribed"] is True
    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None

    mock_mt5_client.market_book_release.assert_called_with(symbol="EURUSD")


def test_post_market_book_unsubscribe_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /market-book/{symbol}/unsubscribe supports Parquet output."""
    test_app = cast("FastAPI", client.app)
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.market_book_cleanup_client = mock_mt5_client

    response = client.post(
        "/market-book/EURUSD/unsubscribe?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    mock_mt5_client.market_book_release.assert_called_with(symbol="EURUSD")


def test_post_market_book_unsubscribe_validates_symbol_length(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """POST /market-book/{symbol}/unsubscribe rejects oversized symbols."""
    response = client.post(
        f"/market-book/{'X' * 33}/unsubscribe",
        headers=api_headers,
    )

    assert response.status_code == 422


def test_post_market_book_unsubscribe_keeps_cleanup_client_when_needed(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Unsubscribing one symbol keeps cleanup state for remaining symbols."""
    test_app = cast("FastAPI", client.app)
    test_app.state.active_market_book_subscriptions = {"EURUSD", "USDJPY"}
    test_app.state.market_book_cleanup_client = mock_mt5_client

    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert test_app.state.active_market_book_subscriptions == {"USDJPY"}
    assert test_app.state.market_book_cleanup_client is mock_mt5_client


def test_post_market_book_unsubscribe_does_not_mutate_tracking_on_failure(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """Failed unsubscriptions should preserve tracked market-book state."""
    test_app = cast("FastAPI", client.app)
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.market_book_cleanup_client = mock_mt5_client
    mock_mt5_client.market_book_release.return_value = False

    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert test_app.state.active_market_book_subscriptions == {"EURUSD"}
    assert test_app.state.market_book_cleanup_client is mock_mt5_client


def test_market_book_subscriptions_are_released_on_shutdown(
    mock_mt5_client: Mock,
    api_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tracked market-book subscriptions should be released during shutdown."""
    monkeypatch.setattr(health, "get_mt5_client", lambda: mock_mt5_client)
    app.dependency_overrides.clear()
    app.dependency_overrides[dependencies.get_mt5_client] = lambda: mock_mt5_client

    with TestClient(app) as test_client:
        response = test_client.post(
            "/market-book/EURUSD/subscribe",
            headers=api_headers,
        )
        assert response.status_code == 200

    assert mock_mt5_client.market_book_add.call_args_list == [call(symbol="EURUSD")]
    assert mock_mt5_client.market_book_release.call_args_list == [call(symbol="EURUSD")]


def test_openapi_excludes_order_send_endpoint(
    client: TestClient,
) -> None:
    """The removed order-send endpoint should not appear in OpenAPI."""
    openapi = client.get("/openapi.json").json()

    assert "/order/send" not in openapi["paths"]
