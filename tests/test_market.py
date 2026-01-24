"""Contract tests for market data endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


def test_get_rates_from_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/rates/from returns OHLCV data."""
    response = client.get(
        "/api/v1/rates/from",
        params={
            "symbol": "EURUSD",
            "timeframe": 1,
            "date_from": "2024-01-01T00:00:00Z",
            "count": 2,
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["data"][0]["open"] == 1.08500

    mock_mt5_client.copy_rates_from_as_df.assert_called_with(
        symbol="EURUSD",
        timeframe=1,
        date_from=ANY,
        count=2,
    )


def test_get_rates_from_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/rates/from supports Parquet output."""
    response = client.get(
        "/api/v1/rates/from",
        params={
            "symbol": "EURUSD",
            "timeframe": 1,
            "date_from": "2024-01-01T00:00:00Z",
            "count": 2,
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.copy_rates_from_as_df.assert_called_with(
        symbol="EURUSD",
        timeframe=1,
        date_from=ANY,
        count=2,
    )


def test_get_rates_from_pos_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/rates/from-pos supports Parquet output."""
    response = client.get(
        "/api/v1/rates/from-pos",
        params={
            "symbol": "EURUSD",
            "timeframe": 1,
            "start_pos": 0,
            "count": 2,
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.copy_rates_from_pos_as_df.assert_called_with(
        symbol="EURUSD",
        timeframe=1,
        start_pos=0,
        count=2,
    )


def test_get_rates_from_pos_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/rates/from-pos returns JSON by default."""
    response = client.get(
        "/api/v1/rates/from-pos",
        params={
            "symbol": "EURUSD",
            "timeframe": 1,
            "start_pos": 0,
            "count": 2,
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2

    mock_mt5_client.copy_rates_from_pos_as_df.assert_called_with(
        symbol="EURUSD",
        timeframe=1,
        start_pos=0,
        count=2,
    )


def test_get_rates_range_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/rates/range returns data for a range."""
    response = client.get(
        "/api/v1/rates/range",
        params={
            "symbol": "EURUSD",
            "timeframe": 1,
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2

    mock_mt5_client.copy_rates_range_as_df.assert_called_with(
        symbol="EURUSD",
        timeframe=1,
        date_from=ANY,
        date_to=ANY,
    )


def test_get_rates_range_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/rates/range supports Parquet output."""
    response = client.get(
        "/api/v1/rates/range",
        params={
            "symbol": "EURUSD",
            "timeframe": 1,
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.copy_rates_range_as_df.assert_called_with(
        symbol="EURUSD",
        timeframe=1,
        date_from=ANY,
        date_to=ANY,
    )


def test_get_ticks_from_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/ticks/from returns tick data."""
    response = client.get(
        "/api/v1/ticks/from",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "count": 1,
            "flags": 6,
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["bid"] == 1.08500

    mock_mt5_client.copy_ticks_from_as_df.assert_called_with(
        symbol="EURUSD",
        date_from=ANY,
        count=1,
        flags=6,
    )


def test_get_ticks_from_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/ticks/from supports Parquet output."""
    response = client.get(
        "/api/v1/ticks/from",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "count": 1,
            "flags": 6,
            "format": "parquet",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.copy_ticks_from_as_df.assert_called_with(
        symbol="EURUSD",
        date_from=ANY,
        count=1,
        flags=6,
    )


def test_get_ticks_range_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/ticks/range supports Parquet output."""
    response = client.get(
        "/api/v1/ticks/range",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers={**api_headers, "Accept": "application/parquet"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.copy_ticks_range_as_df.assert_called_with(
        symbol="EURUSD",
        date_from=ANY,
        date_to=ANY,
        flags=6,
    )


def test_get_ticks_range_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/ticks/range returns JSON by default."""
    response = client.get(
        "/api/v1/ticks/range",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-02T00:00:00Z",
        },
        headers=api_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1

    mock_mt5_client.copy_ticks_range_as_df.assert_called_with(
        symbol="EURUSD",
        date_from=ANY,
        date_to=ANY,
        flags=6,
    )


def test_get_market_book_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/market-book/{symbol} returns market depth."""
    response = client.get("/api/v1/market-book/EURUSD", headers=api_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["data"][0]["price"] == 1.08500

    mock_mt5_client.market_book_get_as_df.assert_called_with(symbol="EURUSD")


def test_get_market_book_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/market-book/{symbol} supports Parquet output."""
    response = client.get(
        "/api/v1/market-book/EURUSD?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.market_book_get_as_df.assert_called_with(symbol="EURUSD")
