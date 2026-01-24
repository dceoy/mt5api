"""Contract tests for symbol-related endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


def test_get_symbols_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols returns JSON payload with symbols."""
    response = client.get("/api/v1/symbols", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["format"] == "json"
    assert payload["count"] == 2
    assert isinstance(payload["data"], list)
    assert payload["data"][0]["name"] == "EURUSD"

    mock_mt5_client.symbols_get_as_df.assert_called_with(group=None)


def test_get_symbols_supports_group_filter(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols supports group query filter."""
    response = client.get(
        "/api/v1/symbols?group=*USD*",
        headers=api_headers,
    )

    assert response.status_code == 200

    mock_mt5_client.symbols_get_as_df.assert_called_with(group="*USD*")


def test_get_symbols_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols returns Parquet when requested."""
    response = client.get(
        "/api/v1/symbols?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")
    assert "data.parquet" in response.headers.get("content-disposition", "")

    mock_mt5_client.symbols_get_as_df.assert_called_with(group=None)


def test_get_symbol_info_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols/{symbol} returns symbol info."""
    response = client.get("/api/v1/symbols/EURUSD", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["name"] == "EURUSD"

    mock_mt5_client.symbol_info_as_df.assert_called_with(symbol="EURUSD")


def test_get_symbol_info_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols/{symbol} returns Parquet when requested."""
    response = client.get(
        "/api/v1/symbols/EURUSD?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.symbol_info_as_df.assert_called_with(symbol="EURUSD")


def test_get_symbol_tick_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols/{symbol}/tick returns tick info."""
    response = client.get("/api/v1/symbols/EURUSD/tick", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["bid"] == 1.08500

    mock_mt5_client.symbol_info_tick_as_df.assert_called_with(symbol="EURUSD")


def test_get_symbol_tick_accepts_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/symbols/{symbol}/tick supports Parquet via Accept."""
    headers = {**api_headers, "Accept": "application/parquet"}
    response = client.get("/api/v1/symbols/EURUSD/tick", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.symbol_info_tick_as_df.assert_called_with(symbol="EURUSD")
