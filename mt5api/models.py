"""Pydantic models for API request validation and response serialization."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import StrEnum
from typing import Annotated, Any, Self, TypeAlias

import pdmt5
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SecretStr,
    WithJsonSchema,
    model_validator,
)

_TIMEFRAME_DESCRIPTION = (
    "MetaTrader5 TIMEFRAME constant. Accepts a constant name such as "
    "TIMEFRAME_M1, short aliases such as M1, or the corresponding integer value."
)
_TIMEFRAME_EXAMPLE_NAMES = (
    "TIMEFRAME_M1",
    "TIMEFRAME_M5",
    "TIMEFRAME_M15",
    "TIMEFRAME_M30",
    "TIMEFRAME_H1",
    "TIMEFRAME_H4",
    "TIMEFRAME_D1",
    "TIMEFRAME_W1",
    "TIMEFRAME_MN1",
)
_COPY_TICKS_DESCRIPTION = (
    "MetaTrader5 COPY_TICKS constant. Accepts COPY_TICKS_INFO, "
    "COPY_TICKS_TRADE, COPY_TICKS_ALL, short aliases such as ALL, "
    "or the corresponding integer value."
)
_COPY_TICKS_EXAMPLE_NAMES = (
    "COPY_TICKS_INFO",
    "COPY_TICKS_TRADE",
    "COPY_TICKS_ALL",
)
_ORDER_TYPE_DESCRIPTION = (
    "MetaTrader5 ORDER_TYPE constant. Accepts a constant name such as "
    "ORDER_TYPE_BUY, short aliases such as BUY, or the corresponding integer value."
)
_ORDER_TYPE_EXAMPLE_NAMES = (
    "ORDER_TYPE_BUY",
    "ORDER_TYPE_SELL",
)


def _build_mt5_constant_json_schema(
    *,
    description: str,
    names: tuple[str, ...],
    values: tuple[int, ...],
    examples: list[str],
) -> dict[str, Any]:
    """Build a JSON schema for a name-or-integer MT5 constant parameter.

    Returns:
        The JSON schema fragment for the MT5 constant parameter.
    """
    return {
        "anyOf": [
            {"type": "string", "enum": list(names)},
            {"type": "integer", "enum": list(values)},
        ],
        "description": description,
        "examples": examples,
    }


def get_mt5_timeframe_values() -> tuple[int, ...]:
    """Return all available MT5 timeframe values from pdmt5."""
    return tuple(pdmt5.list_timeframe_values())


def get_mt5_timeframe_names() -> tuple[str, ...]:
    """Return all available MT5 timeframe names from pdmt5."""
    return tuple(pdmt5.list_timeframe_names())


def get_mt5_timeframe_examples() -> list[int]:
    """Return common MT5 timeframe examples from pdmt5."""
    return [pdmt5.TIMEFRAME_MAP[name] for name in _TIMEFRAME_EXAMPLE_NAMES]


def get_mt5_timeframe_example_names() -> list[str]:
    """Return common MT5 timeframe example names."""
    return list(_TIMEFRAME_EXAMPLE_NAMES)


def get_mt5_copy_ticks_values() -> tuple[int, ...]:
    """Return all MT5 COPY_TICKS values from pdmt5."""
    return tuple(pdmt5.list_copy_ticks_values())


def get_mt5_copy_ticks_names() -> tuple[str, ...]:
    """Return all MT5 COPY_TICKS names from pdmt5."""
    return tuple(pdmt5.list_copy_ticks_names())


def get_mt5_copy_ticks_examples() -> list[int]:
    """Return common MT5 COPY_TICKS integer examples."""
    return [pdmt5.COPY_TICKS_MAP[name] for name in _COPY_TICKS_EXAMPLE_NAMES]


def get_mt5_copy_ticks_example_names() -> list[str]:
    """Return common MT5 COPY_TICKS example names."""
    return list(_COPY_TICKS_EXAMPLE_NAMES)


def _validate_mt5_timeframe(value: object) -> int:
    """Validate MT5 timeframe input.

    Returns:
        The validated integer timeframe value.
    """
    return pdmt5.parse_timeframe(value)


def _validate_mt5_copy_ticks(value: object) -> int:
    """Validate MT5 COPY_TICKS input.

    Returns:
        The validated integer COPY_TICKS value.
    """
    return pdmt5.parse_copy_ticks(value)


def get_mt5_order_type_values() -> tuple[int, ...]:
    """Return all available MT5 ORDER_TYPE values from pdmt5."""
    return tuple(pdmt5.list_order_type_values())


def get_mt5_order_type_names() -> tuple[str, ...]:
    """Return all available MT5 ORDER_TYPE names from pdmt5."""
    return tuple(pdmt5.list_order_type_names())


def get_mt5_order_type_examples() -> list[int]:
    """Return common MT5 ORDER_TYPE integer examples."""
    return [pdmt5.ORDER_TYPE_MAP[name] for name in _ORDER_TYPE_EXAMPLE_NAMES]


def get_mt5_order_type_example_names() -> list[str]:
    """Return common MT5 ORDER_TYPE example names."""
    return list(_ORDER_TYPE_EXAMPLE_NAMES)


def _validate_mt5_order_type(value: object) -> int:
    """Validate MT5 ORDER_TYPE input.

    Returns:
        The validated integer ORDER_TYPE value.
    """
    return pdmt5.parse_order_type(value)


Mt5Timeframe: TypeAlias = Annotated[
    int,
    BeforeValidator(_validate_mt5_timeframe),
    WithJsonSchema(
        _build_mt5_constant_json_schema(
            description=_TIMEFRAME_DESCRIPTION,
            names=get_mt5_timeframe_names(),
            values=get_mt5_timeframe_values(),
            examples=get_mt5_timeframe_example_names(),
        ),
        mode="validation",
    ),
]


Mt5CopyTicks: TypeAlias = Annotated[
    int,
    BeforeValidator(_validate_mt5_copy_ticks),
    WithJsonSchema(
        _build_mt5_constant_json_schema(
            description=_COPY_TICKS_DESCRIPTION,
            names=get_mt5_copy_ticks_names(),
            values=get_mt5_copy_ticks_values(),
            examples=get_mt5_copy_ticks_example_names(),
        ),
        mode="validation",
    ),
]


Mt5OrderType: TypeAlias = Annotated[
    int,
    BeforeValidator(_validate_mt5_order_type),
    WithJsonSchema(
        _build_mt5_constant_json_schema(
            description=_ORDER_TYPE_DESCRIPTION,
            names=get_mt5_order_type_names(),
            values=get_mt5_order_type_values(),
            examples=get_mt5_order_type_example_names(),
        ),
        mode="validation",
    ),
]


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
        examples=["/rates/from"],
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
    timeframe: Mt5Timeframe = Field(
        ...,
        description=_TIMEFRAME_DESCRIPTION,
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
    timeframe: Mt5Timeframe = Field(
        ...,
        description=_TIMEFRAME_DESCRIPTION,
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
    timeframe: Mt5Timeframe = Field(
        ...,
        description=_TIMEFRAME_DESCRIPTION,
    )
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
    flags: Mt5CopyTicks = Field(
        default=pdmt5.COPY_TICKS_MAP["COPY_TICKS_ALL"],
        description=_COPY_TICKS_DESCRIPTION,
    )
    format: ResponseFormat | None = Field(default=None)


class TicksRangeRequest(BaseModel):
    """Request parameters for ticks range endpoint."""

    symbol: str = Field(..., description="Symbol name")
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    date_to: datetime = Field(..., description="End date (ISO 8601)")
    flags: Mt5CopyTicks = Field(
        default=pdmt5.COPY_TICKS_MAP["COPY_TICKS_ALL"],
        description=_COPY_TICKS_DESCRIPTION,
    )
    format: ResponseFormat | None = Field(default=None)


class MarketBookRequest(BaseModel):
    """Request parameters for market book endpoint."""

    symbol: str = Field(
        ...,
        description="Symbol name",
        min_length=1,
        max_length=32,
        examples=["EURUSD"],
    )
    format: ResponseFormat | None = Field(default=None)


class MarketBookSubscriptionRequest(BaseModel):
    """Request parameters for market-book subscription endpoints."""

    symbol: str = Field(
        ...,
        description="Symbol name",
        min_length=1,
        max_length=32,
        examples=["EURUSD"],
    )


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


class HistoryTotalRequest(BaseModel):
    """Request parameters for history total count endpoints."""

    date_from: datetime = Field(
        ...,
        description="Start date (ISO 8601 format)",
        examples=["2024-01-01T00:00:00Z"],
    )
    date_to: datetime = Field(
        ...,
        description="End date (ISO 8601 format)",
        examples=["2024-01-02T00:00:00Z"],
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        """Ensure date_from is before date_to.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If date_from is not before date_to.
        """
        if self.date_from >= self.date_to:
            range_error = "date_from must be before date_to"
            raise ValueError(range_error)
        return self


class CalcMarginRequest(BaseModel):
    """Request parameters for margin calculation endpoint."""

    action: Mt5OrderType = Field(
        ...,
        description=_ORDER_TYPE_DESCRIPTION,
    )
    symbol: str = Field(
        ...,
        description="Symbol name",
        examples=["EURUSD"],
    )
    volume: float = Field(
        ...,
        description="Trade volume in lots",
        gt=0,
        examples=[0.1, 1.0],
    )
    price: float = Field(
        ...,
        description="Open price",
        gt=0,
        examples=[1.08500],
    )


class CalcProfitRequest(BaseModel):
    """Request parameters for profit calculation endpoint."""

    action: Mt5OrderType = Field(
        ...,
        description=_ORDER_TYPE_DESCRIPTION,
    )
    symbol: str = Field(
        ...,
        description="Symbol name",
        examples=["EURUSD"],
    )
    volume: float = Field(
        ...,
        description="Trade volume in lots",
        gt=0,
        examples=[0.1, 1.0],
    )
    price_open: float = Field(
        ...,
        description="Open price",
        gt=0,
        examples=[1.08500],
    )
    price_close: float = Field(
        ...,
        description="Close price",
        gt=0,
        examples=[1.09000],
    )


class TradeRequest(BaseModel):
    """Typed MT5 trade request payload used for order validation."""

    model_config = ConfigDict(extra="forbid")

    action: int = Field(
        ...,
        description="MetaTrader5 TRADE_ACTION constant value",
        ge=0,
        examples=[1],
    )
    symbol: str = Field(
        ...,
        description="Symbol name",
        min_length=1,
        max_length=32,
        examples=["EURUSD"],
    )
    volume: float = Field(
        ...,
        description="Trade volume in lots",
        gt=0,
        examples=[0.1, 1.0],
    )
    type: Mt5OrderType = Field(
        ...,
        description=_ORDER_TYPE_DESCRIPTION,
    )
    price: float = Field(
        ...,
        description="Requested price",
        ge=0,
        examples=[1.08500],
    )
    stoplimit: float | None = Field(
        default=None,
        description="Stop-limit price for stop-limit pending orders",
        ge=0,
        examples=[1.08450],
    )
    sl: float | None = Field(
        default=None,
        description="Stop-loss price",
        ge=0,
        examples=[1.08000],
    )
    tp: float | None = Field(
        default=None,
        description="Take-profit price",
        ge=0,
        examples=[1.09000],
    )
    deviation: int | None = Field(
        default=None,
        description="Maximum allowed price deviation in points",
        ge=0,
        examples=[10],
    )
    magic: int | None = Field(
        default=None,
        description="Expert Advisor identifier",
        ge=0,
        examples=[123456],
    )
    comment: str | None = Field(
        default=None,
        description="Trade request comment",
        min_length=1,
        examples=["validation-check"],
    )
    type_filling: int | None = Field(
        default=None,
        description="MetaTrader5 ORDER_FILLING constant value",
        ge=0,
        examples=[1],
    )
    type_time: int | None = Field(
        default=None,
        description="MetaTrader5 ORDER_TIME constant value",
        ge=0,
        examples=[0],
    )
    expiration: datetime | None = Field(
        default=None,
        description="Expiration time for timed pending orders",
        examples=["2024-01-02T00:00:00Z"],
    )
    order: int | None = Field(
        default=None,
        description="Pending order ticket",
        ge=0,
        examples=[123456],
    )
    position: int | None = Field(
        default=None,
        description="Open position ticket",
        ge=0,
        examples=[123456],
    )
    position_by: int | None = Field(
        default=None,
        description="Opposite position ticket",
        ge=0,
        examples=[654321],
    )


class OrderCheckRequest(BaseModel):
    """Request parameters for order check endpoint."""

    request: TradeRequest = Field(
        ...,
        description="Trade request dictionary for order validation",
    )


class LoginRequest(BaseModel):
    """Request body for the MT5 connection login endpoint."""

    model_config = ConfigDict(extra="forbid")

    login: int = Field(
        ...,
        description="Trading account login",
        gt=0,
        examples=[12345678],
    )
    password: SecretStr = Field(
        ...,
        description="Trading account password (never echoed in responses)",
        min_length=1,
        max_length=128,
        examples=["s3cret"],
    )
    server: str = Field(
        ...,
        description="Trading server name",
        min_length=1,
        max_length=128,
        examples=["MetaQuotes-Demo"],
    )
    timeout: int | None = Field(
        default=None,
        description="Connection timeout in milliseconds",
        gt=0,
        examples=[60000],
    )


class LoginResponse(BaseModel):
    """Response body for the MT5 connection login endpoint."""

    login: int = Field(
        description="Trading account login that was used to connect",
        examples=[12345678],
    )
    server: str = Field(
        description="Trading server the client connected to",
        examples=["MetaQuotes-Demo"],
    )
    timeout: int | None = Field(
        default=None,
        description="Connection timeout in milliseconds, if specified",
        examples=[60000],
    )
    connected: bool = Field(
        description="Whether the MT5 client successfully connected",
        examples=[True],
    )


class SymbolSelectRequest(BaseModel):
    """Request parameters for symbol select endpoint."""

    symbol: str = Field(
        ...,
        description="Symbol name",
        min_length=1,
        max_length=32,
        examples=["EURUSD"],
    )
    enable: bool = Field(
        default=True,
        description="True to show symbol in MarketWatch, False to hide",
    )
