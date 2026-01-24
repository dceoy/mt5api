# Data Model: REST API Request and Response Models

**Feature**: REST API for MetaTrader 5 Data Access
**Branch**: `041-mt5-rest-api`
**Date**: 2026-01-02

## Overview

This document defines all pydantic models used for request validation and response serialization in the MT5 REST API. Models are organized by functional area and map directly to `Mt5DataClient` methods.

## Common Types

### ResponseFormat

Format preference for API responses.

```python
from enum import Enum

class ResponseFormat(str, Enum):
    """Supported response formats."""
    JSON = "json"
    PARQUET = "parquet"
```

**Usage**: Query parameter or Accept header mapping

- `?format=json` or `Accept: application/json` → ResponseFormat.JSON
- `?format=parquet` or `Accept: application/parquet` → ResponseFormat.PARQUET

---

## Request Models

### Health & System Endpoints

#### No request model needed

- `GET /api/v1/health` - No parameters
- `GET /api/v1/version` - No parameters

---

### Symbol Endpoints

#### SymbolsRequest

Get list of available symbols with optional filtering.

```python
from pydantic import BaseModel, Field

class SymbolsRequest(BaseModel):
    """Request parameters for symbols list endpoint."""

    group: str | None = Field(
        default=None,
        description="Symbol group filter (e.g., '*USD*', 'Forex*')",
        examples=["*USD*", "Forex*", "Crypto*"]
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Response format (json or parquet)"
    )
```

**Maps to**: `Mt5DataClient.symbols_get_as_df(group=...)`

#### SymbolInfoRequest

Get detailed information for a specific symbol.

```python
class SymbolInfoRequest(BaseModel):
    """Request parameters for symbol info endpoint."""

    symbol: str = Field(
        ...,
        description="Symbol name (e.g., EURUSD)",
        min_length=1,
        max_length=32,
        examples=["EURUSD", "BTCUSD", "US30"]
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Response format"
    )
```

**Maps to**: `Mt5DataClient.symbol_info_as_df(symbol=...)`

#### SymbolTickRequest

Get latest tick for a symbol.

```python
class SymbolTickRequest(BaseModel):
    """Request parameters for symbol tick endpoint."""

    symbol: str = Field(
        ...,
        description="Symbol name",
        examples=["EURUSD"]
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Response format"
    )
```

**Maps to**: `Mt5DataClient.symbol_info_tick_as_df(symbol=...)`

---

### Market Data Endpoints

#### RatesFromRequest

Get historical rates from a specific date.

```python
from datetime import datetime

class RatesFromRequest(BaseModel):
    """Request parameters for rates from date endpoint."""

    symbol: str = Field(..., description="Symbol name")
    timeframe: int = Field(
        ...,
        description="Timeframe in minutes (MT5 constant)",
        ge=1,
        examples=[1, 5, 15, 60, 240, 1440]
    )
    date_from: datetime = Field(
        ...,
        description="Start date (ISO 8601 format)",
        examples=["2024-01-01T00:00:00Z"]
    )
    count: int = Field(
        ...,
        description="Number of candles to retrieve",
        ge=1,
        le=100000,
        examples=[100, 1000]
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Response format"
    )
```

**Maps to**: `Mt5DataClient.copy_rates_from_as_df(symbol, timeframe, date_from, count)`

#### RatesFromPosRequest

Get historical rates from a position index.

```python
class RatesFromPosRequest(BaseModel):
    """Request parameters for rates from position endpoint."""

    symbol: str = Field(..., description="Symbol name")
    timeframe: int = Field(..., description="Timeframe in minutes", ge=1)
    start_pos: int = Field(
        ...,
        description="Start position (0 = current bar)",
        ge=0,
        examples=[0, 100, 1000]
    )
    count: int = Field(
        ...,
        description="Number of candles",
        ge=1,
        le=100000
    )
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.copy_rates_from_pos_as_df(symbol, timeframe, start_pos, count)`

#### RatesRangeRequest

Get historical rates for a date range.

```python
class RatesRangeRequest(BaseModel):
    """Request parameters for rates range endpoint."""

    symbol: str = Field(..., description="Symbol name")
    timeframe: int = Field(..., description="Timeframe in minutes", ge=1)
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    date_to: datetime = Field(..., description="End date (ISO 8601)")
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.copy_rates_range_as_df(symbol, timeframe, date_from, date_to)`

#### TicksFromRequest

Get tick data from a specific date.

```python
class TicksFromRequest(BaseModel):
    """Request parameters for ticks from date endpoint."""

    symbol: str = Field(..., description="Symbol name")
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    count: int = Field(
        ...,
        description="Number of ticks",
        ge=1,
        le=100000
    )
    flags: int = Field(
        default=6,  # COPY_TICKS_ALL
        description="Tick flags (MT5 constant: 2=INFO, 4=TRADE, 6=ALL)",
        ge=0,
        examples=[2, 4, 6]
    )
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.copy_ticks_from_as_df(symbol, date_from, count, flags)`

#### TicksRangeRequest

Get tick data for a date range.

```python
class TicksRangeRequest(BaseModel):
    """Request parameters for ticks range endpoint."""

    symbol: str = Field(..., description="Symbol name")
    date_from: datetime = Field(..., description="Start date (ISO 8601)")
    date_to: datetime = Field(..., description="End date (ISO 8601)")
    flags: int = Field(
        default=6,
        description="Tick flags",
        examples=[2, 4, 6]
    )
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.copy_ticks_range_as_df(symbol, date_from, date_to, flags)`

#### MarketBookRequest

Get market depth (DOM) for a symbol.

```python
class MarketBookRequest(BaseModel):
    """Request parameters for market book endpoint."""

    symbol: str = Field(..., description="Symbol name")
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.market_book_get_as_df(symbol)`

---

### Account & Terminal Endpoints

#### AccountInfoRequest / TerminalInfoRequest

```python
class AccountInfoRequest(BaseModel):
    """Request parameters for account info endpoint."""
    format: ResponseFormat = Field(default=ResponseFormat.JSON)

class TerminalInfoRequest(BaseModel):
    """Request parameters for terminal info endpoint."""
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**:

- `Mt5DataClient.account_info_as_df()`
- `Mt5DataClient.terminal_info_as_df()`

---

### Trading Endpoints

#### PositionsRequest

Get current open positions.

```python
class PositionsRequest(BaseModel):
    """Request parameters for positions endpoint."""

    symbol: str | None = Field(
        default=None,
        description="Filter by symbol"
    )
    group: str | None = Field(
        default=None,
        description="Filter by group pattern"
    )
    ticket: int | None = Field(
        default=None,
        description="Filter by position ticket",
        ge=0
    )
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.positions_get_as_df(symbol, group, ticket)`

#### OrdersRequest

Get current pending orders.

```python
class OrdersRequest(BaseModel):
    """Request parameters for orders endpoint."""

    symbol: str | None = Field(default=None)
    group: str | None = Field(default=None)
    ticket: int | None = Field(default=None, ge=0)
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.orders_get_as_df(symbol, group, ticket)`

---

### History Endpoints

#### HistoryOrdersRequest

Get historical orders.

```python
class HistoryOrdersRequest(BaseModel):
    """Request parameters for historical orders endpoint."""

    date_from: datetime | None = Field(
        default=None,
        description="Start date (required if ticket/position not specified)"
    )
    date_to: datetime | None = Field(
        default=None,
        description="End date (required if ticket/position not specified)"
    )
    group: str | None = Field(default=None, description="Group pattern")
    symbol: str | None = Field(default=None, description="Symbol filter")
    ticket: int | None = Field(default=None, description="Order ticket", ge=0)
    position: int | None = Field(default=None, description="Position ticket", ge=0)
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Validation**: Either (date_from AND date_to) OR (ticket OR position) must be provided.

**Maps to**: `Mt5DataClient.history_orders_get_as_df(date_from, date_to, group, symbol, ticket, position)`

#### HistoryDealsRequest

Get historical deals.

```python
class HistoryDealsRequest(BaseModel):
    """Request parameters for historical deals endpoint."""

    date_from: datetime | None = Field(default=None)
    date_to: datetime | None = Field(default=None)
    group: str | None = Field(default=None)
    symbol: str | None = Field(default=None)
    ticket: int | None = Field(default=None, ge=0)
    position: int | None = Field(default=None, ge=0)
    format: ResponseFormat = Field(default=ResponseFormat.JSON)
```

**Maps to**: `Mt5DataClient.history_deals_get_as_df(date_from, date_to, group, symbol, ticket, position)`

---

## Response Models

### Success Responses

All successful data responses follow this pattern:

```python
class DataResponse(BaseModel):
    """Generic successful data response."""

    data: list[dict[str, Any]] | dict[str, Any] = Field(
        ...,
        description="Response data as list of records or single record"
    )
    count: int = Field(..., description="Number of records returned")
    format: ResponseFormat = Field(..., description="Response format used")
```

**For JSON responses**: Returns DataResponse with data field containing records
**For Parquet responses**: Returns binary Parquet file with appropriate Content-Type header

### HealthResponse

```python
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., examples=["healthy", "unhealthy"])
    mt5_connected: bool = Field(..., description="MT5 terminal connection status")
    mt5_version: str | None = Field(None, description="MT5 version if connected")
    api_version: str = Field(..., description="API version")
```

### ErrorResponse

```python
class ErrorResponse(BaseModel):
    """Error response following RFC 7807 Problem Details."""

    type: str = Field(
        ...,
        description="Error type URI",
        examples=["about:blank", "/errors/mt5-disconnected"]
    )
    title: str = Field(..., description="Short error summary")
    status: int = Field(..., description="HTTP status code", ge=400, le=599)
    detail: str = Field(..., description="Detailed error explanation")
    instance: str | None = Field(
        None,
        description="Request URI that caused error"
    )
```

**Example error responses**:

```json
{
  "type": "/errors/mt5-disconnected",
  "title": "MT5 Terminal Not Connected",
  "status": 503,
  "detail": "MetaTrader5 terminal is not running or not logged in. Please start MT5 and login.",
  "instance": "/api/v1/symbols/EURUSD"
}
```

```json
{
  "type": "/errors/invalid-symbol",
  "title": "Symbol Not Found",
  "status": 404,
  "detail": "Symbol 'INVALID' does not exist or is not available on this broker.",
  "instance": "/api/v1/symbols/INVALID"
}
```

```json
{
  "type": "/errors/validation-error",
  "title": "Request Validation Failed",
  "status": 400,
  "detail": "count must be positive (got: -10)",
  "instance": "/api/v1/rates/from"
}
```

---

## Model Validation Rules

### Date Validation

- All datetime fields accept ISO 8601 format: `YYYY-MM-DDTHH:MM:SS[.ffffff][Z or ±HH:MM]`
- Timezone-aware datetimes preferred (Z suffix for UTC)
- For range queries: `date_from` must be before `date_to`

### Numeric Validation

- `count`: Must be positive (ge=1), max 100000 to prevent memory issues
- `timeframe`: Must be positive (ge=1), represents minutes
- `ticket`, `position`: Must be non-negative (ge=0)
- `start_pos`: Must be non-negative (ge=0)

### String Validation

- `symbol`: 1-32 characters, uppercase recommended
- `group`: Wildcard patterns supported (`*`, `?`)

### Custom Validators

#### HistoryRequest Validation

```python
from pydantic import model_validator

class HistoryOrdersRequest(BaseModel):
    # ... fields ...

    @model_validator(mode='after')
    def validate_date_or_ticket(self):
        """Ensure either date range or ticket/position is provided."""
        has_dates = self.date_from is not None and self.date_to is not None
        has_filter = self.ticket is not None or self.position is not None

        if not has_dates and not has_filter:
            raise ValueError(
                "Either (date_from AND date_to) or (ticket OR position) must be provided"
            )

        if has_dates and self.date_from >= self.date_to:
            raise ValueError(
                f"date_from ({self.date_from}) must be before date_to ({self.date_to})"
            )

        return self
```

---

## DataFrame to Response Conversion

### JSON Conversion

```python
def dataframe_to_json(df: pd.DataFrame) -> dict:
    """Convert DataFrame to JSON response."""
    records = df.to_dict(orient="records")
    return {
        "data": records,
        "count": len(records),
        "format": "json"
    }
```

### Parquet Conversion

```python
def dataframe_to_parquet(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Parquet bytes."""
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", compression="snappy")
    buffer.seek(0)
    return buffer.getvalue()
```

**Headers for Parquet response**:

```
Content-Type: application/parquet
Content-Disposition: attachment; filename="data.parquet"
```

---

## Model Mapping Summary

| Endpoint                 | HTTP Method | Request Model        | Mt5DataClient Method             |
| ------------------------ | ----------- | -------------------- | -------------------------------- |
| `/health`                | GET         | None                 | `version()`                      |
| `/version`               | GET         | None                 | `version_as_df()`                |
| `/symbols`               | GET         | SymbolsRequest       | `symbols_get_as_df(group)`       |
| `/symbols/{symbol}`      | GET         | SymbolInfoRequest    | `symbol_info_as_df(symbol)`      |
| `/symbols/{symbol}/tick` | GET         | SymbolTickRequest    | `symbol_info_tick_as_df(symbol)` |
| `/rates/from`            | GET         | RatesFromRequest     | `copy_rates_from_as_df(...)`     |
| `/rates/from-pos`        | GET         | RatesFromPosRequest  | `copy_rates_from_pos_as_df(...)` |
| `/rates/range`           | GET         | RatesRangeRequest    | `copy_rates_range_as_df(...)`    |
| `/ticks/from`            | GET         | TicksFromRequest     | `copy_ticks_from_as_df(...)`     |
| `/ticks/range`           | GET         | TicksRangeRequest    | `copy_ticks_range_as_df(...)`    |
| `/market-book/{symbol}`  | GET         | MarketBookRequest    | `market_book_get_as_df(symbol)`  |
| `/account`               | GET         | AccountInfoRequest   | `account_info_as_df()`           |
| `/terminal`              | GET         | TerminalInfoRequest  | `terminal_info_as_df()`          |
| `/positions`             | GET         | PositionsRequest     | `positions_get_as_df(...)`       |
| `/orders`                | GET         | OrdersRequest        | `orders_get_as_df(...)`          |
| `/history/orders`        | GET         | HistoryOrdersRequest | `history_orders_get_as_df(...)`  |
| `/history/deals`         | GET         | HistoryDealsRequest  | `history_deals_get_as_df(...)`   |

---

## Implementation Notes

1. **Model Location**: All models in `pdmt5/api/models.py`
2. **Validation**: Pydantic v2 validators with detailed error messages
3. **Serialization**: Use pydantic's `model_dump()` for JSON serialization
4. **Type Safety**: All models use strict type hints for pyright validation
5. **Documentation**: Model docstrings become OpenAPI schema descriptions
6. **Examples**: Field examples appear in Swagger UI for testing
