"""Contract tests for market data endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY

from mt5api.models import (
    get_mt5_copy_ticks_example_names,
    get_mt5_copy_ticks_names,
    get_mt5_copy_ticks_values,
    get_mt5_timeframe_example_names,
    get_mt5_timeframe_names,
    get_mt5_timeframe_values,
)
from tests.mt5_constants import Mt5CopyTicks, Mt5Timeframe

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


VALID_TIMEFRAME_VALUES = list(get_mt5_timeframe_values())
VALID_TIMEFRAME_NAMES = list(get_mt5_timeframe_names())
TIMEFRAME_EXAMPLES = get_mt5_timeframe_example_names()
VALID_TICK_FLAG_VALUES = list(get_mt5_copy_ticks_values())
VALID_TICK_FLAG_NAMES = list(get_mt5_copy_ticks_names())
TICK_FLAG_EXAMPLES = get_mt5_copy_ticks_example_names()
TIMEFRAME_M1 = int(Mt5Timeframe.TIMEFRAME_M1)
COPY_TICKS_ALL = int(Mt5CopyTicks.COPY_TICKS_ALL)


def test_get_rates_from_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /rates/from returns OHLCV data."""
    response = client.get(
        "/rates/from",
        params={
            "symbol": "EURUSD",
            "timeframe": "TIMEFRAME_M1",
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
        timeframe=TIMEFRAME_M1,
        date_from=ANY,
        count=2,
    )


def test_get_rates_from_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /rates/from supports Parquet output."""
    response = client.get(
        "/rates/from",
        params={
            "symbol": "EURUSD",
            "timeframe": TIMEFRAME_M1,
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
        timeframe=TIMEFRAME_M1,
        date_from=ANY,
        count=2,
    )


def test_get_rates_from_pos_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /rates/from-pos supports Parquet output."""
    response = client.get(
        "/rates/from-pos",
        params={
            "symbol": "EURUSD",
            "timeframe": TIMEFRAME_M1,
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
        timeframe=TIMEFRAME_M1,
        start_pos=0,
        count=2,
    )


def test_get_rates_from_pos_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /rates/from-pos returns JSON by default."""
    response = client.get(
        "/rates/from-pos",
        params={
            "symbol": "EURUSD",
            "timeframe": TIMEFRAME_M1,
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
        timeframe=TIMEFRAME_M1,
        start_pos=0,
        count=2,
    )


def test_get_rates_range_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /rates/range returns data for a range."""
    response = client.get(
        "/rates/range",
        params={
            "symbol": "EURUSD",
            "timeframe": TIMEFRAME_M1,
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
        timeframe=TIMEFRAME_M1,
        date_from=ANY,
        date_to=ANY,
    )


def test_get_rates_range_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /rates/range supports Parquet output."""
    response = client.get(
        "/rates/range",
        params={
            "symbol": "EURUSD",
            "timeframe": TIMEFRAME_M1,
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
        timeframe=TIMEFRAME_M1,
        date_from=ANY,
        date_to=ANY,
    )


def test_get_rates_from_rejects_invalid_mt5_timeframe(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """GET /rates/from rejects unsupported MT5 timeframe values."""
    response = client.get(
        "/rates/from",
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


def test_get_rates_from_rejects_invalid_mt5_timeframe_name(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """GET /rates/from rejects unsupported MT5 timeframe names."""
    response = client.get(
        "/rates/from",
        params={
            "symbol": "EURUSD",
            "timeframe": "TIMEFRAME_INVALID",
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
    """Rates endpoints should expose MT5 timeframe names and integer values."""
    openapi = client.get("/openapi.json").json()
    paths = (
        "/rates/from",
        "/rates/from-pos",
        "/rates/range",
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

        string_schema = next(
            schema for schema in timeframe_schema["anyOf"] if schema["type"] == "string"
        )
        integer_schema = next(
            schema
            for schema in timeframe_schema["anyOf"]
            if schema["type"] == "integer"
        )

        assert sorted(string_schema["enum"]) == sorted(VALID_TIMEFRAME_NAMES)
        assert sorted(integer_schema["enum"]) == sorted(VALID_TIMEFRAME_VALUES)
        assert timeframe_schema["examples"] == TIMEFRAME_EXAMPLES
        assert (
            timeframe_schema["description"]
            == "MetaTrader5 TIMEFRAME constant. Accepts a constant name such as "
            "TIMEFRAME_M1 or the short alias M1, or the corresponding integer value."
        )


def test_get_ticks_from_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /ticks/from returns tick data."""
    response = client.get(
        "/ticks/from",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "count": 1,
            "flags": "COPY_TICKS_ALL",
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
        flags=COPY_TICKS_ALL,
    )


def test_get_ticks_from_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /ticks/from supports Parquet output."""
    response = client.get(
        "/ticks/from",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "count": 1,
            "flags": COPY_TICKS_ALL,
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
        flags=COPY_TICKS_ALL,
    )


def test_get_ticks_range_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /ticks/range supports Parquet output."""
    response = client.get(
        "/ticks/range",
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
        flags=COPY_TICKS_ALL,
    )


def test_get_ticks_range_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /ticks/range returns JSON by default."""
    response = client.get(
        "/ticks/range",
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
        flags=COPY_TICKS_ALL,
    )


def test_get_ticks_from_rejects_invalid_mt5_copy_ticks_name(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """GET /ticks/from rejects unsupported MT5 COPY_TICKS names."""
    response = client.get(
        "/ticks/from",
        params={
            "symbol": "EURUSD",
            "date_from": "2024-01-01T00:00:00Z",
            "count": 1,
            "flags": "COPY_TICKS_INVALID",
        },
        headers=api_headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "flags"


def test_openapi_documents_mt5_copy_ticks_consistently(
    client: TestClient,
) -> None:
    """Tick endpoints should expose MT5 COPY_TICKS names and integer values."""
    openapi = client.get("/openapi.json").json()
    paths = ("/ticks/from", "/ticks/range")

    for path in paths:
        parameters = openapi["paths"][path]["get"]["parameters"]
        flag_parameter = next(
            parameter for parameter in parameters if parameter["name"] == "flags"
        )
        flag_schema = flag_parameter["schema"]

        string_schema = next(
            schema for schema in flag_schema["anyOf"] if schema["type"] == "string"
        )
        integer_schema = next(
            schema for schema in flag_schema["anyOf"] if schema["type"] == "integer"
        )

        assert sorted(string_schema["enum"]) == sorted(VALID_TICK_FLAG_NAMES)
        assert sorted(integer_schema["enum"]) == sorted(VALID_TICK_FLAG_VALUES)
        assert flag_schema["examples"] == TICK_FLAG_EXAMPLES
        assert (
            flag_schema["description"]
            == "MetaTrader5 COPY_TICKS constant. Accepts COPY_TICKS_INFO, "
            "COPY_TICKS_TRADE, COPY_TICKS_ALL, short aliases such as ALL, "
            "or the corresponding integer value."
        )


def test_get_market_book_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /market-book/{symbol} returns market depth."""
    response = client.get("/market-book/EURUSD", headers=api_headers)

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
    """GET /market-book/{symbol} supports Parquet output."""
    response = client.get(
        "/market-book/EURUSD?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.market_book_get_as_df.assert_called_with(symbol="EURUSD")
