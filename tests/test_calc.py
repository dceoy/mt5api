"""Contract tests for trading calculation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pdmt5.mt5 import Mt5RuntimeError

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


@pytest.mark.parametrize(
    "params",
    [
        {
            "action": 99,
            "symbol": "EURUSD",
            "volume": 0.1,
            "price": 1.08500,
        },
        {
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0,
            "price": 1.08500,
        },
        {
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0.1,
            "price": 0,
        },
    ],
)
def test_get_calc_margin_validates_query_params(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    params: dict[str, str | float | int],
) -> None:
    """GET /calc/margin rejects invalid query parameter combinations."""
    response = client.get(
        "/calc/margin",
        params=params,
        headers=api_headers,
    )

    assert response.status_code == 422
    mock_mt5_client.order_calc_margin.assert_not_called()


@pytest.mark.parametrize(
    "params",
    [
        {
            "action": 99,
            "symbol": "EURUSD",
            "volume": 0.1,
            "price_open": 1.08500,
            "price_close": 1.09000,
        },
        {
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0,
            "price_open": 1.08500,
            "price_close": 1.09000,
        },
        {
            "action": "ORDER_TYPE_BUY",
            "symbol": "EURUSD",
            "volume": 0.1,
            "price_open": 1.08500,
            "price_close": 0,
        },
    ],
)
def test_get_calc_profit_validates_query_params(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
    params: dict[str, str | float | int],
) -> None:
    """GET /calc/profit rejects invalid query parameter combinations."""
    response = client.get(
        "/calc/profit",
        params=params,
        headers=api_headers,
    )

    assert response.status_code == 422
    mock_mt5_client.order_calc_profit.assert_not_called()


def test_get_calc_margin_returns_service_unavailable_on_mt5_error(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /calc/margin surfaces MT5 runtime failures as 503 responses."""
    mock_mt5_client.order_calc_margin.side_effect = Mt5RuntimeError(
        "order_calc_margin returned None"
    )

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

    assert response.status_code == 503
    payload = response.json()
    assert payload["title"] == "MT5 Terminal Error"
    assert "order_calc_margin returned None" in payload["detail"]


def test_get_calc_profit_returns_service_unavailable_on_mt5_error(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /calc/profit surfaces MT5 runtime failures as 503 responses."""
    mock_mt5_client.order_calc_profit.side_effect = Mt5RuntimeError(
        "order_calc_profit returned None"
    )

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

    assert response.status_code == 503
    payload = response.json()
    assert payload["title"] == "MT5 Terminal Error"
    assert "order_calc_profit returned None" in payload["detail"]
