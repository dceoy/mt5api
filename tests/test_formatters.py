"""Tests for response formatters and format negotiation."""

from __future__ import annotations

from typing import cast

import pandas as pd
import pytest
from fastapi.responses import Response

from pdmt5.api.formatters import (
    format_dataframe_to_json,
    format_dataframe_to_parquet,
    format_dict_to_json,
    format_dict_to_parquet,
    format_response,
)
from pdmt5.api.models import DataResponse, ResponseFormat


def test_format_dataframe_to_json_returns_data_response() -> None:
    """Test DataFrame to JSON formatting."""
    dataframe = pd.DataFrame([
        {"symbol": "EURUSD", "bid": 1.08500, "ask": 1.08520},
        {"symbol": "GBPUSD", "bid": 1.25000, "ask": 1.25020},
    ])

    result = format_dataframe_to_json(dataframe)

    assert result.count == 2
    assert result.format == ResponseFormat.JSON
    assert isinstance(result.data, list)
    assert len(result.data) == 2
    assert result.data[0]["symbol"] == "EURUSD"


def test_format_dataframe_to_json_with_index_orientation() -> None:
    """Test DataFrame to JSON formatting with non-records orientation."""
    dataframe = pd.DataFrame(
        [
            {"symbol": "EURUSD", "bid": 1.08500},
            {"symbol": "GBPUSD", "bid": 1.25000},
        ],
        index=["first", "second"],
    )

    result = format_dataframe_to_json(dataframe, orient="index")

    assert isinstance(result.data, dict)


def test_format_dict_to_json_returns_data_response() -> None:
    """Test dictionary to JSON formatting."""
    data = {"version": "5.0.4321", "build": 4321}

    result = format_dict_to_json(data)

    assert result.count == 1
    assert result.format == ResponseFormat.JSON
    assert isinstance(result.data, dict)
    assert result.data["version"] == "5.0.4321"


def test_format_dataframe_to_parquet_returns_binary() -> None:
    """Test DataFrame to Parquet formatting."""
    dataframe = pd.DataFrame([
        {"symbol": "EURUSD", "bid": 1.08500, "ask": 1.08520},
        {"symbol": "GBPUSD", "bid": 1.25000, "ask": 1.25020},
    ])

    response = format_dataframe_to_parquet(dataframe)

    assert response.media_type == "application/parquet"
    assert "data.parquet" in response.headers.get("Content-Disposition", "")

    # Verify StreamingResponse - async generator tested in integration
    assert hasattr(response, "body_iterator")


def test_format_dict_to_parquet_returns_binary() -> None:
    """Test dictionary to Parquet formatting."""
    data = {"version": "5.0.4321", "build": 4321}

    response = format_dict_to_parquet(data)

    assert response.media_type == "application/parquet"

    # Verify StreamingResponse - async generator tested in integration
    assert hasattr(response, "body_iterator")


@pytest.mark.parametrize(
    ("data", "response_format", "expected_type"),
    [
        (pd.DataFrame([{"symbol": "EURUSD"}]), ResponseFormat.JSON, DataResponse),
        (pd.DataFrame([{"symbol": "EURUSD"}]), ResponseFormat.PARQUET, Response),
        ({"symbol": "EURUSD"}, ResponseFormat.JSON, DataResponse),
        ({"symbol": "EURUSD"}, ResponseFormat.PARQUET, Response),
    ],
)
def test_format_response_routes_by_data_and_format(
    data: pd.DataFrame | dict[str, object],
    response_format: ResponseFormat,
    expected_type: type[object],
) -> None:
    """Test format_response routing for data type and format."""
    result = format_response(data, response_format)

    assert isinstance(result, expected_type)


def test_format_response_rejects_invalid_data_type() -> None:
    """Test format_response rejects unsupported data types."""
    with pytest.raises(TypeError, match=r"DataFrame|dict"):
        format_response([1, 2, 3], ResponseFormat.JSON)  # type: ignore[arg-type]


def test_format_response_rejects_invalid_format() -> None:
    """Test format_response rejects unsupported formats."""
    invalid_format = cast("ResponseFormat", "xml")

    with pytest.raises(ValueError, match="Unsupported response format"):
        format_response({"symbol": "EURUSD"}, invalid_format)


def test_get_response_format_from_query_parameter() -> None:
    """Test format negotiation via query parameter."""
    from pdmt5.api.dependencies import get_response_format  # noqa: PLC0415

    # Query parameter takes priority
    result = get_response_format(
        accept="application/json",
        format_param=ResponseFormat.PARQUET,
    )

    assert result == ResponseFormat.PARQUET


def test_get_response_format_from_accept_header() -> None:
    """Test format negotiation via Accept header."""
    from pdmt5.api.dependencies import get_response_format  # noqa: PLC0415

    result = get_response_format(accept="application/parquet", format_param=None)

    assert result == ResponseFormat.PARQUET


def test_get_response_format_defaults_to_json() -> None:
    """Test format negotiation defaults to JSON."""
    from pdmt5.api.dependencies import get_response_format  # noqa: PLC0415

    result = get_response_format(accept=None, format_param=None)

    assert result == ResponseFormat.JSON


def test_get_response_format_from_accept_header_json() -> None:
    """Test format negotiation via JSON Accept header."""
    from pdmt5.api.dependencies import get_response_format  # noqa: PLC0415

    result = get_response_format(accept="application/json", format_param=None)

    assert result == ResponseFormat.JSON


def test_get_response_format_from_unrecognized_accept_header() -> None:
    """Test format negotiation defaults to JSON for unknown Accept header."""
    from pdmt5.api.dependencies import get_response_format  # noqa: PLC0415

    result = get_response_format(accept="text/plain", format_param=None)

    assert result == ResponseFormat.JSON


def test_get_response_format_handles_complex_accept_header() -> None:
    """Test format negotiation with complex Accept header."""
    from pdmt5.api.dependencies import get_response_format  # noqa: PLC0415

    result = get_response_format(
        accept="text/html, application/parquet;q=0.9, */*;q=0.8",
        format_param=None,
    )

    assert result == ResponseFormat.PARQUET
