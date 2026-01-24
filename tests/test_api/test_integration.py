"""Integration tests for REST API journeys."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_symbol_retrieval_journey(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Verify symbol listing and detail retrieval works end-to-end."""
    symbols_response = client.get("/api/v1/symbols", headers=api_headers)
    assert symbols_response.status_code == 200

    symbols_payload = symbols_response.json()
    assert symbols_payload["count"] >= 1
    symbol_name = symbols_payload["data"][0]["name"]

    info_response = client.get(
        f"/api/v1/symbols/{symbol_name}",
        headers=api_headers,
    )
    assert info_response.status_code == 200

    tick_response = client.get(
        f"/api/v1/symbols/{symbol_name}/tick",
        headers=api_headers,
    )
    assert tick_response.status_code == 200


def test_account_monitoring_journey(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Verify account and terminal info endpoints respond."""
    account_response = client.get("/api/v1/account", headers=api_headers)
    assert account_response.status_code == 200

    terminal_response = client.get("/api/v1/terminal", headers=api_headers)
    assert terminal_response.status_code == 200


def test_history_journey(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Verify history endpoints respond with required filters."""
    orders_response = client.get(
        "/api/v1/history/orders",
        params={
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers=api_headers,
    )
    assert orders_response.status_code == 200

    deals_response = client.get(
        "/api/v1/history/deals",
        params={"ticket": 123456},
        headers=api_headers,
    )
    assert deals_response.status_code == 200


def test_positions_and_orders_journey(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Verify positions and orders endpoints respond."""
    positions_response = client.get("/api/v1/positions", headers=api_headers)
    assert positions_response.status_code == 200

    orders_response = client.get("/api/v1/orders", headers=api_headers)
    assert orders_response.status_code == 200
