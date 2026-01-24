"""Contract tests for history, positions, and orders endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


def test_get_history_orders_with_date_range(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/history/orders accepts date range."""
    response = client.get(
        "/api/v1/history/orders",
        params={
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0

    mock_mt5_client.history_orders_get_as_df.assert_called_with(
        date_from=ANY,
        date_to=ANY,
        group=None,
        symbol=None,
        ticket=None,
        position=None,
    )


def test_get_history_orders_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/history/orders supports Parquet output."""
    response = client.get(
        "/api/v1/history/orders",
        params={
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.history_orders_get_as_df.assert_called_with(
        date_from=ANY,
        date_to=ANY,
        group=None,
        symbol=None,
        ticket=None,
        position=None,
    )


def test_get_history_deals_with_ticket(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/history/deals accepts ticket filter."""
    response = client.get(
        "/api/v1/history/deals",
        params={"ticket": 123456},
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0

    mock_mt5_client.history_deals_get_as_df.assert_called_with(
        date_from=None,
        date_to=None,
        group=None,
        symbol=None,
        ticket=123456,
        position=None,
    )


def test_get_history_deals_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/history/deals supports Parquet output."""
    response = client.get(
        "/api/v1/history/deals?ticket=123456&format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.history_deals_get_as_df.assert_called_with(
        date_from=None,
        date_to=None,
        group=None,
        symbol=None,
        ticket=123456,
        position=None,
    )


def test_get_positions_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/positions returns open positions."""
    response = client.get("/api/v1/positions", headers=api_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["ticket"] == 123456

    mock_mt5_client.positions_get_as_df.assert_called_with(
        symbol=None,
        group=None,
        ticket=None,
    )


def test_get_positions_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/positions supports Parquet output."""
    response = client.get("/api/v1/positions?format=parquet", headers=api_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.positions_get_as_df.assert_called_with(
        symbol=None,
        group=None,
        ticket=None,
    )


def test_get_orders_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/orders returns pending orders."""
    response = client.get("/api/v1/orders", headers=api_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["ticket"] == 789012

    mock_mt5_client.orders_get_as_df.assert_called_with(
        symbol=None,
        group=None,
        ticket=None,
    )


def test_get_orders_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/orders supports Parquet output."""
    response = client.get("/api/v1/orders?format=parquet", headers=api_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.orders_get_as_df.assert_called_with(
        symbol=None,
        group=None,
        ticket=None,
    )
