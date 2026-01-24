# Feature Specification: Mt5 DataFrame Client

**Feature Branch**: `043-mt5-dataframe-client`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "Mt5 data client with pandas DataFrame conversions and validation"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Retrieve MT5 Data as DataFrames (Priority: P1)

As a Python data analyst, I want MT5 data returned as pandas DataFrames so I can analyze market data and account state without manual conversion.

**Why this priority**: DataFrame output is the primary value of this client for analysis workflows.

**Independent Test**: Can be fully tested by calling data retrieval methods and validating that DataFrames are returned with expected columns and types.

**Acceptance Scenarios**:

1. **Given** a configured client, **When** I request rates or ticks, **Then** I receive a pandas DataFrame with time columns converted to datetime.
2. **Given** a configured client, **When** I request account or symbol info, **Then** I receive a pandas DataFrame representing the MT5 response.

---

### User Story 2 - Use Validated Connection Configuration (Priority: P2)

As a Python user, I want to provide MT5 connection parameters via a configuration object so I can reuse validated credentials and settings.

**Why this priority**: Configuration validation reduces user error and enables reliable automation.

**Independent Test**: Can be fully tested by instantiating the configuration with valid and invalid inputs and verifying validation behavior.

**Acceptance Scenarios**:

1. **Given** valid connection parameters, **When** I create a configuration object, **Then** the client can initialize and login using that configuration.
2. **Given** invalid connection parameters, **When** I create a configuration object, **Then** I receive a validation error describing the issue.

---

### User Story 3 - Consistent Empty Results and Input Validation (Priority: P3)

As a Python user, I want consistent empty DataFrame results and validation for date ranges and counts so I can rely on predictable behavior in pipelines.

**Why this priority**: Predictable empty results prevent pipeline failures and reduce defensive coding.

**Independent Test**: Can be fully tested by requesting data for empty ranges and invalid inputs and validating the resulting DataFrames or errors.

**Acceptance Scenarios**:

1. **Given** a date range with no data, **When** I request history or rates, **Then** I receive an empty DataFrame with expected columns.
2. **Given** invalid date ranges or negative counts, **When** I request data, **Then** the client raises a clear validation error.

---

### Edge Cases

- What happens when the MT5 API returns None or an empty result set?
- How does the client handle invalid date ranges (start after end)?
- What happens when count or position arguments are negative or zero?
- How does the client behave when time conversion is disabled?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST provide a configuration object for MT5 connection parameters with validation.
- **FR-002**: The system MUST return pandas DataFrames for MT5 data retrieval operations.
- **FR-003**: The system MUST convert time-related fields to datetime by default, with an opt-out toggle.
- **FR-004**: The system MUST allow callers to set a DataFrame index when a valid index key is provided.
- **FR-005**: The system MUST validate date ranges, counts, and position arguments for data retrieval requests.
- **FR-006**: The system MUST return empty DataFrames for valid requests that yield no data.
- **FR-007**: The system MUST provide consistent error messages when validation fails or MT5 returns an error.

### Key Entities _(include if feature involves data)_

- **Mt5Config**: Represents validated connection and session parameters.
- **DataFrameResult**: Represents MT5 responses as pandas DataFrames.
- **RateSeries**: Represents OHLCV time-series data.
- **TickSeries**: Represents tick-level time-series data.
- **AccountSnapshot**: Represents current account state in tabular form.
- **SymbolSnapshot**: Represents symbol metadata and tick state in tabular form.

## Dependencies

- [specs/042-mt5-core-client/spec.md](specs/042-mt5-core-client/spec.md)
- [specs/045-mt5-utils/spec.md](specs/045-mt5-utils/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Each data retrieval method returns a pandas DataFrame for both non-empty and empty results.
- **SC-002**: Time fields in returned DataFrames are converted to datetime when conversion is enabled.
- **SC-003**: Invalid input ranges or counts are rejected with explicit validation errors.
- **SC-004**: A user can initialize a client from configuration and retrieve at least one dataset as a DataFrame in a single session.
