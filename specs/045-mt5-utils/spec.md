# Feature Specification: Mt5 Utilities

**Feature Branch**: `045-mt5-utils`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "Utility decorators for time conversion and DataFrame index management"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Automatic Time Conversion (Priority: P1)

As a data analyst, I want MT5 time values converted to datetime objects automatically so I can work with time-series data without manual transformations.

**Why this priority**: Time conversion is a core usability improvement for all DataFrame outputs.

**Independent Test**: Can be fully tested by passing dictionaries and DataFrames with time fields and verifying datetime conversion.

**Acceptance Scenarios**:

1. **Given** a response dictionary with time fields, **When** the conversion decorator runs, **Then** time values are converted to datetime objects.
2. **Given** a DataFrame with time columns, **When** conversion is enabled, **Then** time columns are converted to pandas datetime dtype.

---

### User Story 2 - Optional Indexing of DataFrames (Priority: P2)

As a data analyst, I want to set a DataFrame index automatically when a valid index column is provided so I can work with indexed time-series data easily.

**Why this priority**: Indexed DataFrames improve analytical workflows and reduce repetitive code.

**Independent Test**: Can be fully tested by returning DataFrames with index keys and verifying index setting behavior.

**Acceptance Scenarios**:

1. **Given** a DataFrame and a valid index key, **When** the index decorator runs, **Then** the DataFrame is returned with that index.
2. **Given** an empty DataFrame, **When** the index decorator runs, **Then** it returns the DataFrame unchanged.

---

### User Story 3 - Safe and Predictable Decorator Behavior (Priority: P3)

As a library user, I want these utilities to fail loudly on invalid types and be opt-out when needed so I can rely on predictable behavior.

**Why this priority**: Predictability and clear errors are essential for stable data pipelines.

**Independent Test**: Can be fully tested by passing unsupported return types and disabling conversion.

**Acceptance Scenarios**:

1. **Given** a method returns a non-dict or non-DataFrame, **When** the conversion decorator runs, **Then** it raises a clear TypeError.
2. **Given** conversion is disabled, **When** the method runs, **Then** the output is returned without time conversion.

---

### Edge Cases

- What happens when a time column is already datetime dtype?
- How does conversion behave with missing or null time values?
- What happens when index key does not exist in the DataFrame?
- How does conversion handle millisecond vs second timestamps?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST provide a decorator that converts time fields in dicts and DataFrames to datetime.
- **FR-002**: The system MUST detect millisecond vs second time fields using naming conventions.
- **FR-003**: The system MUST allow callers to disable time conversion per call.
- **FR-004**: The system MUST provide a decorator to set DataFrame indexes when a valid index column is provided.
- **FR-005**: The system MUST return empty DataFrames unchanged.
- **FR-006**: The system MUST raise explicit TypeError exceptions for unsupported result types.

### Key Entities _(include if feature involves data)_

- **TimeConversionRule**: Represents the field naming conventions for time conversion.
- **IndexKey**: Represents a DataFrame column name used for indexing.
- **ConvertedResult**: Represents a dict or DataFrame with converted time fields.

## Dependencies

- None.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Time conversion occurs for both dict and DataFrame results when enabled.
- **SC-002**: Index setting occurs only when the DataFrame is non-empty and contains the index key.
- **SC-003**: Invalid types result in predictable exceptions rather than silent failures.
