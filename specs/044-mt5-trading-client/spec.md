# Feature Specification: Mt5 Trading Client

**Feature Branch**: `044-mt5-trading-client`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "Mt5 trading client with order management, dry run, and position tools"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Close Positions Safely (Priority: P1)

As a trader, I want to close open positions by symbol or in bulk so I can manage exposure quickly and safely.

**Why this priority**: Position management is the core trading operation required for real-world usage.

**Independent Test**: Can be fully tested by opening test positions and validating that close requests return structured results for each symbol.

**Acceptance Scenarios**:

1. **Given** open positions for a symbol, **When** I request to close that symbol, **Then** the client returns per-position results indicating success or failure.
2. **Given** no open positions, **When** I request to close positions, **Then** the client returns an empty but well-defined result.

---

### User Story 2 - Dry Run Trading Validation (Priority: P2)

As a strategy developer, I want a dry run mode that validates orders without execution so I can test trading logic safely.

**Why this priority**: Dry run mode reduces risk when developing and testing strategies.

**Independent Test**: Can be fully tested by enabling dry run and confirming that orders are checked rather than executed.

**Acceptance Scenarios**:

1. **Given** dry run mode enabled, **When** I submit a close operation, **Then** the client validates the order without executing a real trade.
2. **Given** dry run mode disabled, **When** I submit a close operation, **Then** the client attempts live execution.

---

### User Story 3 - Compute Trading Metrics (Priority: P3)

As a trader, I want access to trading metrics (margin, volume, spread, and position metrics) so I can assess risk and performance.

**Why this priority**: Metrics enable informed decision-making and strategy evaluation.

**Independent Test**: Can be fully tested by calling metric methods and validating numeric outputs for known inputs.

**Acceptance Scenarios**:

1. **Given** a symbol and account state, **When** I request minimum margin or volume calculations, **Then** I receive numeric results.
2. **Given** open positions, **When** I request position metrics, **Then** I receive a DataFrame with computed fields.

---

### Edge Cases

- What happens when the market is closed or trading is disabled?
- How does the client handle insufficient margin or invalid volume?
- What happens when there are no open positions for a requested symbol?
- How does the client behave when dry run mode is enabled but MT5 rejects validation?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST provide trading operations for closing open positions by symbol, list of symbols, or all symbols.
- **FR-002**: The system MUST provide a dry run mode that validates orders without executing trades.
- **FR-003**: The system MUST return structured per-symbol trade results for trading operations.
- **FR-004**: The system MUST expose trading metric calculations (margin, volume by margin, spread ratio).
- **FR-005**: The system MUST expose position-level metrics derived from current positions.
- **FR-006**: The system MUST surface trading errors as explicit trading exceptions with actionable messages.
- **FR-007**: The system MUST allow customization of order parameters such as filling mode, deviation, and comments.

### Key Entities _(include if feature involves data)_

- **TradeRequest**: Represents a close or market order request with parameters.
- **TradeResult**: Represents per-order execution or validation outcomes.
- **PositionMetrics**: Represents computed metrics for open positions.
- **SymbolGroup**: Represents a symbol or set of symbols targeted for trading actions.

## Dependencies

- [specs/043-mt5-dataframe-client/spec.md](specs/043-mt5-dataframe-client/spec.md)
- [specs/045-mt5-utils/spec.md](specs/045-mt5-utils/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A user can close positions for a specific symbol and receive a structured result for each attempted close.
- **SC-002**: Dry run mode returns validation results without executing live trades.
- **SC-003**: Metric methods return numeric outputs or empty results with no unhandled exceptions.
- **SC-004**: At least one end-to-end test validates closing positions and collecting results in both dry run and live modes (where live mode is possible).
