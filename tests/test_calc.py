"""Contract tests for trading calculation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.mt5_constants import Mt5OrderType

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


def test_get_calc_margin_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /calc/margin returns calculated margin."""
    response = client.get(
        "/calc/margin",
        params={
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0.1,
            "price": 1.08500,
        },
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["margin"] == 108.50

    mock_mt5_client.order_calc_margin.assert_called_with(
        action=int(Mt5OrderType.ORDER_TYPE_BUY),
        symbol="EURUSD",
        volume=0.1,
        price=1.085,
    )


def test_get_calc_margin_accepts_integer_action(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /calc/margin accepts integer action value."""
    response = client.get(
        "/calc/margin",
        params={
            "action": int(Mt5OrderType.ORDER_TYPE_SELL),
            "symbol": "EURUSD",
            "volume": 1.0,
            "price": 1.08500,
        },
        headers=api_headers,
    )

    assert response.status_code == 200

    mock_mt5_client.order_calc_margin.assert_called_with(
        action=int(Mt5OrderType.ORDER_TYPE_SELL),
        symbol="EURUSD",
        volume=1.0,
        price=1.085,
    )


def test_get_calc_margin_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /calc/margin supports Parquet output."""
    response = client.get(
        "/calc/margin",
        params={
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0.1,
            "price": 1.08500,
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.order_calc_margin.assert_called_with(
        action=int(Mt5OrderType.ORDER_TYPE_BUY),
        symbol="EURUSD",
        volume=0.1,
        price=1.085,
    )


def test_get_calc_profit_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /calc/profit returns calculated profit."""
    response = client.get(
        "/calc/profit",
        params={
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0.1,
            "price_open": 1.08500,
            "price_close": 1.09000,
        },
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["profit"] == 50.0

    mock_mt5_client.order_calc_profit.assert_called_with(
        action=int(Mt5OrderType.ORDER_TYPE_BUY),
        symbol="EURUSD",
        volume=0.1,
        price_open=1.085,
        price_close=1.09,
    )


def test_get_calc_profit_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,  # noqa: ARG001
) -> None:
    """GET /calc/profit supports Parquet output."""
    response = client.get(
        "/calc/profit",
        params={
            "action": "ORDER_TYPE_SELL",
            "symbol": "EURUSD",
            "volume": 1.0,
            "price_open": 1.09000,
            "price_close": 1.08500,
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
