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
    """GET /history/orders accepts date range."""
    response = client.get(
        "/history/orders",
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
    """GET /history/orders supports Parquet output."""
    response = client.get(
        "/history/orders",
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
    """GET /history/deals accepts ticket filter."""
    response = client.get(
        "/history/deals",
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
    """GET /history/deals supports Parquet output."""
    response = client.get(
        "/history/deals?ticket=123456&format=parquet",
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
    """GET /positions returns open positions."""
    response = client.get("/positions", headers=api_headers)

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
    """GET /positions supports Parquet output."""
    response = client.get("/positions?format=parquet", headers=api_headers)

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
    """GET /orders returns pending orders."""
    response = client.get("/orders", headers=api_headers)

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
    """GET /orders supports Parquet output."""
    response = client.get("/orders?format=parquet", headers=api_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.orders_get_as_df.assert_called_with(
        symbol=None,
        group=None,
        ticket=None,
    )


def test_get_orders_total_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /orders/total returns active orders count."""
    response = client.get("/orders/total", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["total"] == 3

    mock_mt5_client.orders_total.assert_called_with()


def test_get_positions_total_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /positions/total returns open positions count."""
    response = client.get("/positions/total", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["total"] == 5

    mock_mt5_client.positions_total.assert_called_with()


def test_get_history_orders_total_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /history/orders/total returns historical orders count."""
    response = client.get(
        "/history/orders/total",
        params={
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["total"] == 42

    mock_mt5_client.history_orders_total.assert_called_with(
        date_from=ANY,
        date_to=ANY,
    )


def test_get_history_deals_total_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /history/deals/total returns historical deals count."""
    response = client.get(
        "/history/deals/total",
        params={
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers=api_headers,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["total"] == 37

    mock_mt5_client.history_deals_total.assert_called_with(
        date_from=ANY,
        date_to=ANY,
    )


def test_get_history_orders_total_requires_date_range(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """GET /history/orders/total requires both date_from and date_to."""
    response = client.get(
        "/history/orders/total",
        params={"date_from": "2024-01-01T00:00:00Z"},
        headers=api_headers,
    )

    assert response.status_code == 422
