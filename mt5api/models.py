"""Pydantic models for API request validation and response serialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from enum import StrEnum
from functools import cache, cached_property
from typing import TYPE_CHECKING, Annotated, Any, LiteralString, Self, TypeAlias, cast

from pdmt5.mt5 import Mt5Client
from pydantic import BaseModel, BeforeValidator, Field, WithJsonSchema, model_validator
from pydantic_core import PydanticCustomError

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


class ResponseFormat(StrEnum):
    """Response format enumeration."""

    JSON = "json"
    PARQUET = "parquet"


_TIMEFRAME_DESCRIPTION = (
    "MetaTrader5 TIMEFRAME constant. Accepts a constant name such as "
    "TIMEFRAME_M1 or the corresponding integer value."
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
    "COPY_TICKS_TRADE, COPY_TICKS_ALL, or the corresponding integer value."
)
_COPY_TICKS_NAMES = (
    "COPY_TICKS_INFO",
    "COPY_TICKS_TRADE",
    "COPY_TICKS_ALL",
)
_TIMEFRAME_VALIDATION_DESCRIPTION = "MetaTrader5 TIMEFRAME constant"
_COPY_TICKS_VALIDATION_DESCRIPTION = "MetaTrader5 COPY_TICKS constant"


@dataclass(frozen=True)
class Mt5ConstantSpec:
    """Metadata and cached values for an MT5 constant family."""

    validation_description: str
    schema_description: str
    prefix: str = ""
    names: tuple[str, ...] = ()
    example_names: tuple[str, ...] = ()

    @cached_property
    def members(self) -> dict[str, int]:
        """Return MT5 constant names and values from the pdmt5 MT5 module copy."""
        mt5 = _get_mt5_module()
        if self.names:
            return {name: int(getattr(mt5, name)) for name in self.names}
        return {
            name: int(getattr(mt5, name))
            for name in dir(mt5)
            if name.startswith(self.prefix) and isinstance(getattr(mt5, name), int)
        }

    @cached_property
    def sorted_names(self) -> tuple[str, ...]:
        """Return sorted MT5 constant names."""
        return tuple(sorted(self.members))

    @cached_property
    def sorted_values(self) -> tuple[int, ...]:
        """Return sorted MT5 constant values."""
        return tuple(sorted(self.members.values()))

    @cached_property
    def example_values(self) -> list[int]:
        """Return MT5 constant value examples."""
        return [self.members[name] for name in self.example_names]

    @cached_property
    def example_name_list(self) -> list[str]:
        """Return MT5 constant name examples."""
        return list(self.example_names)


@cache
def _get_mt5_module() -> ModuleType:
    """Return the MetaTrader5 module used by pdmt5."""
    factory = cast(
        "Callable[[], ModuleType]", Mt5Client.model_fields["mt5"].default_factory
    )
    return factory()


_TIMEFRAME_SPEC = Mt5ConstantSpec(
    validation_description=_TIMEFRAME_VALIDATION_DESCRIPTION,
    schema_description=_TIMEFRAME_DESCRIPTION,
    prefix="TIMEFRAME_",
    example_names=_TIMEFRAME_EXAMPLE_NAMES,
)
_COPY_TICKS_SPEC = Mt5ConstantSpec(
    validation_description=_COPY_TICKS_VALIDATION_DESCRIPTION,
    schema_description=_COPY_TICKS_DESCRIPTION,
    names=_COPY_TICKS_NAMES,
    example_names=_COPY_TICKS_NAMES,
)


def _parse_mt5_constant(
    value: object,
    *,
    spec: Mt5ConstantSpec,
) -> int:
    """Parse an MT5 constant name or integer value.

    Returns:
        The validated integer constant value.

    Raises:
        PydanticCustomError: If the value type is not supported.
        ValueError: If the value is not a supported constant name or integer.
    """
    type_error_code = "mt5_constant_type"
    type_error_template: LiteralString = (
        "{description} must be specified by constant name or integer value"
    )
    type_error_context = {"description": spec.validation_description}
    type_error_message = type_error_template.format(**type_error_context)
    if isinstance(value, str):
        if value in spec.members:
            return spec.members[value]
        try:
            value = int(value)
        except ValueError as error:
            raise ValueError(type_error_message) from error

    if isinstance(value, bool) or not isinstance(value, int):
        raise PydanticCustomError(
            type_error_code,
            type_error_template,
            type_error_context,
        )

    parsed_value = value

    if parsed_value not in spec.members.values():
        error_message = (
            f"Unsupported {spec.validation_description.lower()} value: {parsed_value}"
        )
        raise ValueError(error_message)

    return parsed_value


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
    """Return all available MT5 timeframe values from the pdmt5 MT5 module copy."""
    return _TIMEFRAME_SPEC.sorted_values


def get_mt5_timeframe_names() -> tuple[str, ...]:
    """Return all available MT5 timeframe names from the pdmt5 MT5 module copy."""
    return _TIMEFRAME_SPEC.sorted_names


def get_mt5_timeframe_examples() -> list[int]:
    """Return common MT5 timeframe examples from the pdmt5 MT5 module copy."""
    return _TIMEFRAME_SPEC.example_values


def get_mt5_timeframe_example_names() -> list[str]:
    """Return common MT5 timeframe example names."""
    return _TIMEFRAME_SPEC.example_name_list


def get_mt5_copy_ticks_values() -> tuple[int, ...]:
    """Return all MT5 COPY_TICKS values from the pdmt5 MT5 module copy."""
    return _COPY_TICKS_SPEC.sorted_values


def get_mt5_copy_ticks_names() -> tuple[str, ...]:
    """Return all MT5 COPY_TICKS names from the pdmt5 MT5 module copy."""
    return _COPY_TICKS_SPEC.sorted_names


def get_mt5_copy_ticks_examples() -> list[int]:
    """Return common MT5 COPY_TICKS integer examples."""
    return _COPY_TICKS_SPEC.example_values


def get_mt5_copy_ticks_example_names() -> list[str]:
    """Return common MT5 COPY_TICKS example names."""
    return _COPY_TICKS_SPEC.example_name_list


def _validate_mt5_timeframe(value: object) -> int:
    """Validate MT5 timeframe input.

    Returns:
        The validated integer timeframe value.
    """
    return _parse_mt5_constant(value, spec=_TIMEFRAME_SPEC)


def _validate_mt5_copy_ticks(value: object) -> int:
    """Validate MT5 COPY_TICKS input.

    Returns:
        The validated integer COPY_TICKS value.
    """
    return _parse_mt5_constant(value, spec=_COPY_TICKS_SPEC)


Mt5Timeframe: TypeAlias = Annotated[
    int,
    BeforeValidator(_validate_mt5_timeframe),
    WithJsonSchema(
        _build_mt5_constant_json_schema(
            description=_TIMEFRAME_SPEC.schema_description,
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
            description=_COPY_TICKS_SPEC.schema_description,
            names=get_mt5_copy_ticks_names(),
            values=get_mt5_copy_ticks_values(),
            examples=get_mt5_copy_ticks_example_names(),
        ),
        mode="validation",
    ),
]


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
        default=_COPY_TICKS_SPEC.members["COPY_TICKS_ALL"],
        description=_COPY_TICKS_DESCRIPTION,
    )
    format: ResponseFormat | None = Field(default=None)


class TicksRangeRequest(BaseModel):
    """Request parameters for ticks range endpoint."""

    symbol: str = Field(..., description="Symbol name")
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    date_to: datetime = Field(..., description="End date (ISO 8601)")
    flags: Mt5CopyTicks = Field(
        default=_COPY_TICKS_SPEC.members["COPY_TICKS_ALL"],
        description=_COPY_TICKS_DESCRIPTION,
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
