"""Response formatters for JSON and Apache Parquet formats."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any, cast, overload

import pandas as pd
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
from fastapi.responses import Response

from .models import DataResponse, ResponseFormat

_SUPPORTED_RESPONSE_FORMATS = {ResponseFormat.JSON, ResponseFormat.PARQUET}
_INVALID_DATA_MESSAGE = "data must be a pandas DataFrame or dict[str, Any]"

if TYPE_CHECKING:  # pragma: no cover
    from typing import Protocol

    class _PyArrowTable(Protocol):
        """Structural type for the PyArrow table passed to Parquet output."""

    class _PyArrowTableFactory(Protocol):
        """Structural type for the supported PyArrow table factory API."""

        @staticmethod
        def from_pandas(
            dataframe: pd.DataFrame,
            *,
            preserve_index: bool = True,
        ) -> _PyArrowTable: ...

    class _PyArrowModule(Protocol):
        """Structural type for the supported PyArrow module API."""

        Table: _PyArrowTableFactory

    class _PyArrowParquetModule(Protocol):
        """Structural type for the supported PyArrow Parquet API."""

        def write_table(
            self,
            table: _PyArrowTable,
            where: io.BytesIO,
            *,
            compression: str = "snappy",
            use_dictionary: bool = True,
            write_statistics: bool = True,
        ) -> None: ...

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
    """Format DataFrame as JSON response.

    Returns:
        JSON data response.
    """
    if orient == "records":
        data_value: list[dict[str, Any]] | dict[str, Any] = cast(
            "list[dict[str, Any]] | dict[str, Any]",
            dataframe.to_dict(orient=orient),  # type: ignore[arg-type]
        )
    else:
        data_value = cast(
            "list[dict[str, Any]] | dict[str, Any]",
            dataframe.to_dict(orient=orient),  # type: ignore[arg-type]
        )
    return DataResponse(
        data=data_value, count=len(dataframe), format=ResponseFormat.JSON
    )


def format_dict_to_json(data: dict[str, Any]) -> DataResponse:
    """Format dictionary as JSON response.

    Returns:
        Single-record JSON data response.
    """
    return DataResponse(data=data, count=1, format=ResponseFormat.JSON)


def format_dataframe_to_parquet(dataframe: pd.DataFrame) -> Response:
    """Format DataFrame as a materialized Apache Parquet response.

    Returns:
        Binary Parquet HTTP response.
    """
    arrow_module = cast(
        "_PyArrowModule",
        pa,  # pyright: ignore[reportUnknownArgumentType]
    )
    parquet_module = cast(
        "_PyArrowParquetModule",
        pq,  # pyright: ignore[reportUnknownArgumentType]
    )
    table = arrow_module.Table.from_pandas(dataframe, preserve_index=False)
    buffer = io.BytesIO()
    parquet_module.write_table(
        table,
        buffer,
        compression="snappy",
        use_dictionary=True,
        write_statistics=True,
    )
    return Response(
        content=buffer.getvalue(),
        media_type="application/parquet",
        headers={"Content-Disposition": "attachment; filename=data.parquet"},
    )


def format_dict_to_parquet(data: dict[str, Any]) -> Response:
    """Format a dictionary as a single-row Apache Parquet response.

    Returns:
        Binary Parquet HTTP response.
    """
    return format_dataframe_to_parquet(pd.DataFrame([data]))


def format_response(
    data: object,
    response_format: ResponseFormat,
) -> DataResponse | Response:
    """Format a DataFrame or mapping as JSON or Parquet.

    Returns:
        JSON model or binary Parquet response.

    Raises:
        ValueError: If the response format is unsupported.
        TypeError: If ``data`` is not a DataFrame or mapping.
    """
    if response_format not in _SUPPORTED_RESPONSE_FORMATS:
        message = f"Unsupported response format: {response_format}"
        raise ValueError(message)
    if isinstance(data, pd.DataFrame):
        if response_format == ResponseFormat.PARQUET:
            return format_dataframe_to_parquet(data)
        return format_dataframe_to_json(data)
    if isinstance(data, dict):
        data = cast("dict[str, Any]", data)
        if response_format == ResponseFormat.PARQUET:
            return format_dict_to_parquet(data)
        return format_dict_to_json(data)
    raise TypeError(_INVALID_DATA_MESSAGE)
