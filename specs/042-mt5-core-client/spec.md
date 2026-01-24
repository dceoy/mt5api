# Feature Specification: Mt5 Core Client

**Feature Branch**: `042-mt5-core-client`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "Mt5 core client for MT5 terminal connection and core operations"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Connect and Manage MT5 Session (Priority: P1)

As a Python user, I want a client that can initialize and shut down a MetaTrader 5 terminal session so I can reliably manage MT5 connections without manual cleanup.

**Why this priority**: Without a dependable connection lifecycle, none of the MT5 operations are usable.

**Independent Test**: Can be fully tested by initializing a terminal session and confirming shutdown executes even after an error, delivering a stable session lifecycle.

**Acceptance Scenarios**:

1. **Given** a valid MT5 installation, **When** I initialize the client and exit a context manager block, **Then** the terminal connection is established and then cleanly closed.
2. **Given** an uninitialized client, **When** I call an MT5 operation, **Then** the client initializes or raises a clear runtime error indicating initialization is required.

---

### User Story 2 - Access Core MT5 Data (Priority: P2)

As a Python user, I want to retrieve core MT5 data (account, terminal, symbols, ticks, rates, and market book) through a single client so I can inspect trading and market state programmatically.

**Why this priority**: Core data access is the main value of the MT5 client beyond connection management.

**Independent Test**: Can be fully tested by calling account, terminal, symbol, tick, and rate retrieval methods and verifying returned values or empty results.

**Acceptance Scenarios**:

1. **Given** an initialized client, **When** I request account or terminal information, **Then** I receive the latest available metadata from MT5.
2. **Given** an initialized client and a valid symbol, **When** I request symbol info or ticks/rates, **Then** I receive market data for that symbol or a well-defined empty result.

---

### User Story 3 - Access Trading and History Operations (Priority: P3)

As a Python user, I want to access orders, positions, and historical data through the core client so I can inspect trading state and past activity.

**Why this priority**: Trading and history queries enable audits and analysis without using higher-level helpers.

**Independent Test**: Can be fully tested by calling order, position, and history retrieval methods and validating the returned structures.

**Acceptance Scenarios**:

1. **Given** an initialized client, **When** I request orders or positions, **Then** I receive the currently available trading state or an empty result.
2. **Given** a date range, **When** I request historical orders or deals, **Then** I receive records within that range or a well-defined empty result.

---

### Edge Cases

- What happens when the MT5 terminal is not installed or cannot be launched?
- How does the system handle attempts to call MT5 operations before initialization?
- What happens when MT5 returns no data for a symbol or date range?
- How does the client behave if the MT5 connection is lost mid-operation?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST provide a client that can initialize and shut down an MT5 terminal session.
- **FR-002**: The system MUST support context manager usage to manage MT5 session lifecycle automatically.
- **FR-003**: The system MUST expose core MT5 data retrieval operations (account, terminal, symbols, ticks, rates, market book).
- **FR-004**: The system MUST expose trading and history retrieval operations (orders, positions, historical orders, historical deals).
- **FR-005**: The system MUST surface MT5 operation failures as explicit runtime errors with actionable messages.
- **FR-006**: The system MUST log MT5 operation outcomes and MT5 last-error status for observability.
- **FR-007**: The system MUST return well-defined empty results when MT5 provides no data instead of crashing.

### Key Entities _(include if feature involves data)_

- **TerminalSession**: Represents the MT5 terminal connection lifecycle state.
- **AccountInfo**: Represents account metadata such as login, balance, and leverage.
- **SymbolInfo**: Represents instrument metadata and current trading conditions.
- **TickData**: Represents tick-level market data for a symbol.
- **RateData**: Represents OHLCV time-series data for a symbol.
- **Order**: Represents a pending order in the terminal.
- **Position**: Represents an open position.
- **Deal**: Represents a historical trade execution.

## Dependencies

- None.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A user can establish and close a terminal session within one context manager block on a correctly configured MT5 installation.
- **SC-002**: All core data retrieval methods either return MT5 data or a defined empty result without raising unhandled exceptions.
- **SC-003**: Operation failures raise a runtime error that includes the MT5 operation name and status code.
- **SC-004**: At least one integration test validates initialization, data retrieval, and shutdown in sequence.
