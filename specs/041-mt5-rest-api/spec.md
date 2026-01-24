# Feature Specification: REST API for MetaTrader 5 Data Access

**Feature Branch**: `041-mt5-rest-api`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Create REST API for MetaTrader 5 data using FastAPI framework. The API should expose endpoints for pdmt5/dataframe.py functionality, supporting both JSON and Apache Parquet response formats."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Market Data Retrieval via HTTP (Priority: P1)

As a trader or analyst, I want to retrieve current market data (symbols, ticks, and rates) through HTTP requests so that I can integrate MT5 data into my web applications, dashboards, or third-party tools without directly connecting to the MT5 terminal.

**Why this priority**: This is the core value proposition - enabling remote access to MT5 market data. Without this, the API provides no value.

**Independent Test**: Can be fully tested by making GET requests to symbol and market data endpoints and verifying correct JSON/Parquet responses with live market data.

**Acceptance Scenarios**:

1. **Given** an authenticated API connection, **When** I request symbol information for "EURUSD", **Then** I receive current symbol data including bid/ask prices, spreads, and trading parameters
2. **Given** valid date range parameters, **When** I request historical OHLCV rates for a symbol, **Then** I receive a time-series of candle data in the requested format (JSON or Parquet)
3. **Given** a request for real-time tick data, **When** I specify a symbol and time parameters, **Then** I receive tick-level price updates with microsecond timestamps
4. **Given** multiple concurrent requests, **When** multiple clients query market data simultaneously, **Then** all requests complete successfully without data corruption or errors

---

### User Story 2 - Account and Terminal Information Access (Priority: P2)

As a trading system administrator, I want to monitor MT5 terminal status and account information through the API so that I can build monitoring dashboards and alerting systems for my trading infrastructure.

**Why this priority**: Essential for operational monitoring but not required for basic market data access. Can be implemented after core market data endpoints.

**Independent Test**: Can be tested independently by requesting account info, terminal status, and version information endpoints without any trading activity.

**Acceptance Scenarios**:

1. **Given** a connected MT5 terminal, **When** I request account information, **Then** I receive account balance, equity, margin, and trading permissions
2. **Given** an API request for terminal info, **When** the terminal is running, **Then** I receive terminal version, build number, and connection status
3. **Given** periodic health checks, **When** I poll the version endpoint, **Then** I can verify the MT5 connection is alive and responsive

---

### User Story 3 - Flexible Data Format Selection (Priority: P3)

As a data scientist or analyst, I want to choose between JSON and Apache Parquet response formats so that I can optimize data transfer size and processing speed based on my use case (web display vs. bulk analytics).

**Why this priority**: Enhances performance and flexibility but the API is fully functional with JSON alone. Parquet is optimization for large datasets.

**Independent Test**: Can be tested by requesting the same data endpoint with different Accept headers or format parameters and comparing response formats and file sizes.

**Acceptance Scenarios**:

1. **Given** a market data request with `Accept: application/json` header, **When** the API processes the request, **Then** I receive data in JSON format with proper content-type headers
2. **Given** a market data request with `Accept: application/parquet` header, **When** the API processes the request, **Then** I receive data as Apache Parquet binary with columnar compression
3. **Given** a large dataset query (>10k records), **When** I request Parquet format, **Then** the response size is significantly smaller than equivalent JSON (typically 50-80% reduction)
4. **Given** a request with no format specification, **When** the API responds, **Then** JSON is returned as the default format

---

### User Story 4 - Historical Trading Data Access (Priority: P4)

As a quantitative analyst, I want to retrieve historical order and deal information through the API so that I can perform backtesting, performance analysis, and audit my trading activity.

**Why this priority**: Important for analysis but not required for live trading or market monitoring. Can be added after market data endpoints are stable.

**Independent Test**: Can be tested independently by querying historical orders and deals endpoints with date ranges and verifying complete transaction history retrieval.

**Acceptance Scenarios**:

1. **Given** a date range for historical data, **When** I request order history, **Then** I receive all orders placed within that period with full details (symbol, type, volume, prices, status)
2. **Given** a specific position ticket, **When** I request deal history, **Then** I receive all deals (fills) associated with that position
3. **Given** historical data queries, **When** the dataset is large (>1000 records), **Then** the API supports pagination to prevent memory overflow

---

### User Story 5 - Active Positions and Orders Monitoring (Priority: P5)

As an active trader, I want to retrieve current open positions and pending orders through the API so that I can monitor my trading activity from external applications.

**Why this priority**: Useful for monitoring but read-only. Does not enable any new trading capabilities. Should be implemented after core market data.

**Independent Test**: Can be tested by placing orders/positions in MT5 terminal and verifying they appear correctly through API endpoints.

**Acceptance Scenarios**:

1. **Given** active positions in the MT5 terminal, **When** I request current positions, **Then** I receive all open positions with current P&L, volume, and symbol information
2. **Given** pending orders in the terminal, **When** I request active orders, **Then** I receive all pending orders with trigger prices and order parameters
3. **Given** optional symbol filters, **When** I request positions for "EURUSD", **Then** I receive only positions for that specific symbol

---

### Edge Cases

- What happens when MT5 terminal is not connected or disconnected during a request?
- How does the system handle requests for non-existent symbols or invalid date ranges?
- What occurs when requesting historical data that exceeds broker's available history?
- How does the API respond when MT5 terminal is in maintenance mode or not logged in?
- What happens when Parquet format is requested but the response library is not installed?
- How are concurrent write requests handled if trading endpoints are added in future?
- What is the behavior when date ranges span across time zones or DST transitions?
- How does the system handle very large result sets (millions of ticks) that could exhaust memory?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST provide HTTP REST endpoints that expose all read-only methods from `Mt5DataClient` class (version, account*info, terminal_info, symbols_get, symbol_info, symbol_info_tick, market_book_get, copy_rates*_, copy*ticks*_, orders_get, positions_get, history_orders_get, history_deals_get)
- **FR-002**: System MUST support both JSON and Apache Parquet response formats for all data endpoints
- **FR-003**: System MUST allow clients to specify response format via Accept header (`application/json`, `application/parquet`) or query parameter (`format=json` or `format=parquet`)
- **FR-004**: System MUST validate all input parameters (symbols, dates, counts, positions) before passing to MT5 client
- **FR-005**: System MUST return appropriate HTTP status codes (200 for success, 400 for bad request, 404 for not found, 500 for server errors, 503 for MT5 unavailable)
- **FR-006**: System MUST handle MT5 connection errors gracefully and return meaningful error messages
- **FR-007**: System MUST convert pandas DataFrames to JSON or Parquet format based on client request
- **FR-008**: System MUST support datetime parameter inputs in ISO 8601 format for all historical data endpoints
- **FR-009**: System MUST provide health check endpoint to verify MT5 terminal connectivity and API availability
- **FR-010**: System MUST log all API requests with timestamps, endpoints, parameters, and response status
- **FR-011**: System MUST default to JSON format when no format is specified in request
- **FR-012**: System MUST preserve all data types (integers, floats, datetimes, strings) when converting between DataFrame and response formats
- **FR-013**: System MUST support optional filtering parameters (symbol, group, ticket) on endpoints that accept them in Mt5DataClient
- **FR-014**: System MUST implement connection pooling or singleton pattern for Mt5DataClient to avoid multiple terminal connections
- **FR-015**: System MUST provide API documentation via OpenAPI/Swagger UI endpoint

### Non-Functional Requirements

- **NFR-001**: API MUST respond to health check requests within 500ms under normal conditions
- **NFR-002**: Parquet responses MUST achieve at least 50% size reduction compared to JSON for datasets >1000 records
- **NFR-003**: System MUST handle at least 100 concurrent requests without degradation
- **NFR-004**: API MUST be deployable as standalone service that can run on same machine as MT5 terminal (Windows requirement)
- **NFR-005**: System MUST follow REST architectural constraints (stateless, cacheable, uniform interface)
- **NFR-006**: API MUST use pydantic models for request validation and response serialization
- **NFR-007**: System MUST maintain backward compatibility with existing pdmt5 library interfaces

### Security & Constraints

- **SEC-001**: System MUST run on Windows platform only (MT5 terminal limitation)
- **SEC-002**: System MUST implement authentication mechanism to prevent unauthorized access (recommended: API key or OAuth2 bearer token)
- **SEC-003**: System MUST NOT expose trading operations (order_check, order_send) in initial version due to security concerns - read-only API only
- **SEC-004**: System MUST validate and sanitize all input parameters to prevent injection attacks
- **SEC-005**: System MUST use HTTPS when deployed in production environments
- **SEC-006**: System MUST implement rate limiting to prevent API abuse and protect MT5 terminal

### Key Entities _(include if feature involves data)_

- **API Server**: FastAPI application instance that handles HTTP requests and routes to appropriate handlers
- **MT5 Connection**: Singleton or pooled instance of Mt5DataClient that maintains connection to MT5 terminal
- **Request Models**: Pydantic models defining valid parameters for each endpoint (symbol, date ranges, timeframes, filters)
- **Response Models**: Pydantic models or DataFrame serializers that convert MT5 data to JSON/Parquet
- **Format Handler**: Component responsible for detecting requested format and converting DataFrame to appropriate response format
- **Error Handler**: Middleware that catches Mt5RuntimeError and other exceptions, converting to appropriate HTTP error responses

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can retrieve symbol information for any valid MT5 symbol through a single HTTP GET request in under 2 seconds
- **SC-002**: System successfully converts and returns historical OHLCV data for 1000+ candles in both JSON and Parquet formats
- **SC-003**: Parquet responses demonstrate 50-80% file size reduction compared to JSON for datasets with >1000 records
- **SC-004**: API documentation (Swagger UI) is automatically generated and allows users to test all endpoints interactively
- **SC-005**: 95% of market data requests complete successfully without errors under normal MT5 terminal operation
- **SC-006**: System handles MT5 disconnection gracefully by returning HTTP 503 with clear error message instead of crashing
- **SC-007**: All 15+ Mt5DataClient read-only methods are accessible via corresponding REST endpoints
- **SC-008**: API can serve 100 concurrent requests with average response time increase <200ms compared to single request
- **SC-009**: Zero security vulnerabilities in dependencies as reported by safety/bandit scanners
- **SC-010**: All endpoints have comprehensive test coverage (>90%) including error cases and format variations

## Assumptions

1. **MT5 Terminal Availability**: Assume MT5 terminal is installed and configured on the Windows machine where API runs
2. **Network Configuration**: Assume API will run locally or within trusted network initially; production deployment with public internet exposure requires additional security hardening
3. **Authentication Scope**: Initial implementation will use simple API key authentication; more sophisticated OAuth2 can be added later if needed
4. **Read-Only Operations**: Trading operations (order placement, modification, cancellation) are explicitly excluded from initial version to reduce security risk
5. **FastAPI Framework**: Assume FastAPI is appropriate choice based on: excellent async support, automatic OpenAPI docs, pydantic integration, and high performance
6. **Parquet Library**: Assume pyarrow or fastparquet will be used for Parquet format support
7. **Single Terminal**: Assume API connects to single MT5 terminal instance; multi-terminal support is future enhancement
8. **Windows-Only**: Accept Windows platform limitation due to MetaTrader5 Python API restriction
9. **Resource Limits**: Assume queries returning >100k records should be paginated or streamed to prevent memory issues
10. **Time Zone Handling**: Assume all datetime parameters are in UTC unless explicitly specified; MT5 broker time conversions are user's responsibility

## Open Questions

None at this time. All critical design decisions have been made based on project context and issue requirements.
