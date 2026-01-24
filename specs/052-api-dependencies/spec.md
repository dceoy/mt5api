# Feature Specification: API Dependencies and MT5 Client Lifecycle

**Feature Branch**: `052-api-dependencies`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "API dependency injection and MT5 client lifecycle"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Reuse a Single MT5 Client (Priority: P1)

As an API operator, I want the API to reuse a single MT5 client instance so that connections are efficient and stable across requests.

**Why this priority**: MT5 connections are stateful; repeated initialization is costly and error-prone.

**Independent Test**: Can be fully tested by issuing multiple requests and verifying the MT5 client is reused and closed on shutdown.

**Acceptance Scenarios**:

1. **Given** multiple API requests, **When** I call data endpoints, **Then** they share a single MT5 client instance.
2. **Given** service shutdown, **When** the shutdown handler runs, **Then** the MT5 client is closed cleanly.

---

### User Story 2 - Run Blocking MT5 Calls Safely (Priority: P2)

As an API operator, I want MT5 calls executed in a threadpool so the async API remains responsive.

**Why this priority**: Blocking MT5 calls can starve the event loop without threadpool execution.

**Independent Test**: Can be fully tested by calling MT5 endpoints under concurrency and verifying the API remains responsive.

**Acceptance Scenarios**:

1. **Given** an async API request, **When** it triggers an MT5 call, **Then** the call executes in a threadpool and returns results.
2. **Given** concurrent requests, **When** MT5 calls are running, **Then** the API remains responsive to other requests.

---

### User Story 3 - Respect Client Response Format Preferences (Priority: P3)

As an API client, I want to specify a response format per request so I can choose JSON or Parquet outputs.

**Why this priority**: Per-request format selection enables diverse client needs.

**Independent Test**: Can be fully tested by calling endpoints with different format parameters and verifying output types.

**Acceptance Scenarios**:

1. **Given** format=json, **When** I call an endpoint, **Then** I receive a JSON response.
2. **Given** format=parquet, **When** I call an endpoint, **Then** I receive a Parquet response.

---

### Edge Cases

- What happens when MT5 initialization fails on first request?
- How does the API behave if the MT5 client becomes disconnected?
- What happens when a response format is unsupported?
- How does the threadpool handle long-running MT5 operations?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST provide a dependency that returns a shared MT5 client instance.
- **FR-002**: The system MUST initialize the MT5 client on first use and reuse it thereafter.
- **FR-003**: The system MUST shut down the MT5 client when the application stops.
- **FR-004**: The system MUST run MT5 calls in a threadpool to avoid blocking the event loop.
- **FR-005**: The system MUST expose a dependency that resolves the response format per request.
- **FR-006**: The system MUST raise clear errors for unsupported response formats.

### Key Entities _(include if feature involves data)_

- **Mt5ClientInstance**: Represents the shared MT5 client used by the API.
- **ThreadpoolTask**: Represents an MT5 call executed off the event loop.
- **ResponseFormatPreference**: Represents the per-request output format selection.

## Dependencies

- [specs/041-mt5-rest-api/spec.md](specs/041-mt5-rest-api/spec.md)
- [specs/042-mt5-core-client/spec.md](specs/042-mt5-core-client/spec.md)
- [specs/043-mt5-dataframe-client/spec.md](specs/043-mt5-dataframe-client/spec.md)
- [specs/046-mt5-api-service/spec.md](specs/046-mt5-api-service/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Multiple requests reuse a single MT5 client instance.
- **SC-002**: MT5 operations run without blocking the main event loop.
- **SC-003**: Response format selection works for both JSON and Parquet outputs.
