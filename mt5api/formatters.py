"""Response formatters for JSON and Apache Parquet formats."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any, overload

import pandas as pd
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
from fastapi.responses import Response

from .models import DataResponse, ResponseFormat

_SUPPORTED_RESPONSE_FORMATS = {ResponseFormat.JSON, ResponseFormat.PARQUET}
_INVALID_DATA_MESSAGE = "data must be a pandas DataFrame or dict[str, Any]"

if TYPE_CHECKING:  # pragma: no cover

    @overload
    def format_response(
        data: pd.DataFrame,
        response_format: ResponseFormat,
    ) -> DataResponse | Response: ...

    @overload
    def format_response(
        data: dict[str, Any],
        response_format: ResponseFormat,
    ) -> DataResponse | Response: ...


def format_dataframe_to_json(
    dataframe: pd.DataFrame,
    *,
    orient: str = "records",
) -> DataResponse:
    """Format DataFrame as JSON response."""
    if orient == "records":
        data_value: list[dict[str, Any]] | dict[str, Any] = dataframe.to_dict(
            orient=orient  # type: ignore[arg-type]
        )
    else:
        data_value = dataframe.to_dict(orient=orient)  # type: ignore[arg-type]

    return DataResponse(
        data=data_value,
        count=len(dataframe),
        format=ResponseFormat.JSON,
    )


def format_dict_to_json(data: dict[str, Any]) -> DataResponse:
    """Format dictionary as JSON response."""
    return DataResponse(
        data=data,
        count=1,
        format=ResponseFormat.JSON,
    )


def format_dataframe_to_parquet(dataframe: pd.DataFrame) -> Response:
    """Format DataFrame as a materialized Apache Parquet response."""
    table = pa.Table.from_pandas(dataframe, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(
        table,
        buffer,
        compression="snappy",
        use_dictionary=True,
        write_statistics=True,
    )
    return Response(
        content=buffer.getvalue(),
        media_type="application/parquet",
        headers={
            "Content-Disposition": "attachment; filename=data.parquet",
        },
    )


def format_dict_to_parquet(data: dict[str, Any]) -> Response:
    """Format a dictionary as a single-row Apache Parquet response."""
    return format_dataframe_to_parquet(pd.DataFrame([data]))


def format_response(
    data: object,
    response_format: ResponseFormat,
) -> DataResponse | Response:
    """Format a DataFrame or mapping as JSON or Parquet."""
    if response_format not in _SUPPORTED_RESPONSE_FORMATS:
        message = f"Unsupported response format: {response_format}"
        raise ValueError(message)

    if isinstance(data, pd.DataFrame):
        if response_format == ResponseFormat.PARQUET:
            return format_dataframe_to_parquet(data)
        return format_dataframe_to_json(data)

    if isinstance(data, dict):
        if response_format == ResponseFormat.PARQUET:
            return format_dict_to_parquet(data)
        return format_dict_to_json(data)

    raise TypeError(_INVALID_DATA_MESSAGE)
