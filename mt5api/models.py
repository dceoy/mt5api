"""Pydantic models for API request validation and response serialization."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator


class ResponseFormat(StrEnum):
    """Response format enumeration."""

    JSON = "json"
    PARQUET = "parquet"


class ErrorResponse(BaseModel):
    """RFC 7807 Problem Details error response model."""

    type: str = Field(
        description="Error type URI",
        examples=["/errors/validation-error"],
    )
    title: str = Field(
        description="Short error summary",
        examples=["Request Validation Failed"],
    )
    status: int = Field(
        description="HTTP status code",
        ge=400,
        le=599,
        examples=[400],
    )
    detail: str = Field(
        description="Detailed error explanation",
        examples=["count must be positive (got: -10)"],
    )
    instance: str | None = Field(
        default=None,
        description="Request URI that caused error",
        examples=["/api/v1/rates/from"],
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        description="API health status",
        examples=["healthy"],
    )
    mt5_connected: bool = Field(
        description="MT5 terminal connection status",
        examples=[True],
    )
    mt5_version: str | None = Field(
        default=None,
        description="MT5 terminal version",
        examples=["5.0.4321"],
    )
    api_version: str = Field(
        description="API version",
        examples=["1.0.0"],
    )


class DataResponse(BaseModel):
    """Generic data response model for market data endpoints."""

    data: list[dict[str, Any]] | dict[str, Any] = Field(
        description="Response data (array for multiple records, object for single)",
    )
    count: int = Field(
        ge=0,
        description="Number of records returned",
        examples=[100],
    )
    format: ResponseFormat = Field(
        description="Response format used",
        examples=[ResponseFormat.JSON],
    )


class SymbolsRequest(BaseModel):
    """Request parameters for symbols list endpoint."""

    group: str | None = Field(
        default=None,
        description="Symbol group filter (e.g., '*USD*', 'Forex*')",
        examples=["*USD*", "Forex*", "Crypto*"],
    )
    format: ResponseFormat | None = Field(
        default=None,
        description="Response format (json or parquet)",
    )


class SymbolInfoRequest(BaseModel):
    """Request parameters for symbol info endpoint."""

    symbol: str = Field(
        ...,
        description="Symbol name (e.g., EURUSD)",
        min_length=1,
        max_length=32,
        examples=["EURUSD", "BTCUSD", "US30"],
    )
    format: ResponseFormat | None = Field(
        default=None,
        description="Response format",
    )


class SymbolTickRequest(BaseModel):
    """Request parameters for symbol tick endpoint."""

    symbol: str = Field(
        ...,
        description="Symbol name",
        examples=["EURUSD"],
    )
    format: ResponseFormat | None = Field(
        default=None,
        description="Response format",
    )


class RatesFromRequest(BaseModel):
    """Request parameters for rates from date endpoint."""

    symbol: str = Field(..., description="Symbol name")
    timeframe: int = Field(
        ...,
        description="Timeframe in minutes (MT5 constant)",
        ge=1,
        examples=[1, 5, 15, 60, 240, 1440],
    )
    date_from: datetime = Field(
        ...,
        description="Start date (ISO 8601 format)",
        examples=["2024-01-01T00:00:00Z"],
    )
    count: int = Field(
        ...,
        description="Number of candles to retrieve",
        ge=1,
        le=100000,
        examples=[100, 1000],
    )
    format: ResponseFormat | None = Field(
        default=None,
        description="Response format",
    )


class RatesFromPosRequest(BaseModel):
    """Request parameters for rates from position endpoint."""

    symbol: str = Field(..., description="Symbol name")
    timeframe: int = Field(
        ...,
        description="Timeframe in minutes",
        ge=1,
    )
    start_pos: int = Field(
        ...,
        description="Start position (0 = current bar)",
        ge=0,
        examples=[0, 100, 1000],
    )
    count: int = Field(
        ...,
        description="Number of candles",
        ge=1,
        le=100000,
    )
    format: ResponseFormat | None = Field(default=None)


class RatesRangeRequest(BaseModel):
    """Request parameters for rates range endpoint."""

    symbol: str = Field(..., description="Symbol name")
    timeframe: int = Field(..., description="Timeframe in minutes", ge=1)
    date_from: datetime = Field(
        ...,
        description="Start date (ISO 8601)",
    )
    date_to: datetime = Field(
        ...,
        description="End date (ISO 8601)",
    )
    format: ResponseFormat | None = Field(default=None)


class TicksFromRequest(BaseModel):
    """Request parameters for ticks from date endpoint."""

    symbol: str = Field(..., description="Symbol name")
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    count: int = Field(
        ...,
        description="Number of ticks",
        ge=1,
        le=100000,
    )
    flags: int = Field(
        default=6,
        description="Tick flags (MT5 constant: 2=INFO, 4=TRADE, 6=ALL)",
        ge=0,
        examples=[2, 4, 6],
    )
    format: ResponseFormat | None = Field(default=None)


class TicksRangeRequest(BaseModel):
    """Request parameters for ticks range endpoint."""

    symbol: str = Field(..., description="Symbol name")
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    date_to: datetime = Field(..., description="End date (ISO 8601)")
    flags: int = Field(
        default=6,
        description="Tick flags",
        examples=[2, 4, 6],
    )
    format: ResponseFormat | None = Field(default=None)


class MarketBookRequest(BaseModel):
    """Request parameters for market book endpoint."""

    symbol: str = Field(..., description="Symbol name")
    format: ResponseFormat | None = Field(default=None)


class PositionsRequest(BaseModel):
    """Request parameters for positions endpoint."""

    symbol: str | None = Field(
        default=None,
        description="Filter by symbol",
    )
    group: str | None = Field(
        default=None,
        description="Filter by group pattern",
    )
    ticket: int | None = Field(
        default=None,
        description="Filter by position ticket",
        ge=0,
    )
    format: ResponseFormat | None = Field(default=None)


class OrdersRequest(BaseModel):
    """Request parameters for orders endpoint."""

    symbol: str | None = Field(default=None)
    group: str | None = Field(default=None)
    ticket: int | None = Field(default=None, ge=0)
    format: ResponseFormat | None = Field(default=None)


class HistoryRequestBase(BaseModel):
    """Shared fields and validation for history endpoints."""

    date_from: datetime | None = Field(
        default=None,
        description="Start date (required if ticket/position not specified)",
    )
    date_to: datetime | None = Field(
        default=None,
        description="End date (required if ticket/position not specified)",
    )
    ticket: int | None = Field(default=None, description="Ticket filter", ge=0)
    position: int | None = Field(default=None, description="Position filter", ge=0)

    @model_validator(mode="after")
    def validate_date_or_ticket(self) -> Self:
        """Ensure either date range or ticket/position is provided.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If required filters are missing or date range is invalid.
        """
        has_dates = self.date_from is not None and self.date_to is not None
        has_filter = self.ticket is not None or self.position is not None

        if not has_dates and not has_filter:
            error_message = (
                "Either (date_from AND date_to) or (ticket OR position) "
                "must be provided"
            )
            raise ValueError(error_message)

        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from >= self.date_to
        ):
            range_error = "date_from must be before date_to"
            raise ValueError(range_error)

        return self


class HistoryOrdersRequest(HistoryRequestBase):
    """Request parameters for historical orders endpoint."""

    group: str | None = Field(default=None, description="Group pattern")
    symbol: str | None = Field(default=None, description="Symbol filter")
    format: ResponseFormat | None = Field(default=None)


class HistoryDealsRequest(HistoryRequestBase):
    """Request parameters for historical deals endpoint."""

    group: str | None = Field(default=None)
    symbol: str | None = Field(default=None)
    format: ResponseFormat | None = Field(default=None)
