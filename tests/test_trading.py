"""Contract tests for trading operation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


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


def test_post_order_send_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /order/send returns order send result."""
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
        "/order/send",
        json=request_body,
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["retcode"] == 10009
    assert payload["data"]["deal"] == 123456789

    mock_mt5_client.order_send_as_dict.assert_called_with(
        request=request_body["request"],
    )


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

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["symbol"] == "EURUSD"
    assert payload["data"]["subscribed"] is True

    mock_mt5_client.market_book_add.assert_called_with(symbol="EURUSD")


def test_post_market_book_unsubscribe_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """POST /market-book/{symbol}/unsubscribe returns result."""
    response = client.post(
        "/market-book/EURUSD/unsubscribe",
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["symbol"] == "EURUSD"
    assert payload["data"]["unsubscribed"] is True

    mock_mt5_client.market_book_release.assert_called_with(symbol="EURUSD")
