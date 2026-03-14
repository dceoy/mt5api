"""Contract tests for market data endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY

from mt5api.models import get_mt5_timeframe_examples, get_mt5_timeframe_values

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


VALID_TIMEFRAME_VALUES = list(get_mt5_timeframe_values())
TIMEFRAME_EXAMPLES = get_mt5_timeframe_examples()


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


def test_get_rates_from_rejects_invalid_mt5_timeframe(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """GET /api/v1/rates/from rejects unsupported MT5 timeframe values."""
    response = client.get(
        "/api/v1/rates/from",
        params={
            "symbol": "EURUSD",
            "timeframe": 60,
            "date_from": "2024-01-01T00:00:00Z",
            "count": 2,
        },
        headers=api_headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "timeframe"


def test_openapi_documents_mt5_timeframes_consistently(
    client: TestClient,
) -> None:
    """Rates endpoints should expose the same MT5 timeframe enum and examples."""
    openapi = client.get("/openapi.json").json()
    paths = (
        "/api/v1/rates/from",
        "/api/v1/rates/from-pos",
        "/api/v1/rates/range",
    )

    for path in paths:
        parameters = openapi["paths"][path]["get"]["parameters"]
        timeframe_parameter = next(
            parameter for parameter in parameters if parameter["name"] == "timeframe"
        )
        timeframe_schema = timeframe_parameter["schema"]

        if "$ref" in timeframe_schema:
            schema_name = timeframe_schema["$ref"].rsplit("/", maxsplit=1)[-1]
            timeframe_schema = openapi["components"]["schemas"][schema_name]

        assert sorted(timeframe_schema["enum"]) == VALID_TIMEFRAME_VALUES
        assert timeframe_schema["examples"] == TIMEFRAME_EXAMPLES
        assert timeframe_schema["description"] == "MetaTrader5 TIMEFRAME constant"


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
