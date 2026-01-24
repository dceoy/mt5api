# Feature Specification: Mt5 API Service

**Feature Branch**: `046-mt5-api-service`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "FastAPI REST service for MT5 data and trading endpoints"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Query MT5 Data Over HTTP (Priority: P1)

As an integrator, I want to query MT5 market and account data via HTTP so I can consume MT5 data from non-Python clients.

**Why this priority**: Remote data access is the core purpose of the API service.

**Independent Test**: Can be fully tested by calling data endpoints and validating JSON responses without executing trades.

**Acceptance Scenarios**:

1. **Given** valid credentials, **When** I call a market data endpoint, **Then** I receive structured JSON data or a defined empty response.
2. **Given** invalid credentials, **When** I call a data endpoint, **Then** I receive an authorization error response.

---

### User Story 2 - Execute or Validate Trading Operations (Priority: P2)

As a trader, I want to submit trading requests over HTTP with an option to validate without execution so I can integrate automation safely.

**Why this priority**: Trading automation requires both safety and remote access.

**Independent Test**: Can be fully tested by submitting dry-run requests and confirming validation responses.

**Acceptance Scenarios**:

1. **Given** dry-run mode, **When** I submit a trade request, **Then** I receive a validation response without execution.
2. **Given** live mode and valid parameters, **When** I submit a trade request, **Then** I receive a trade result response.

---

### User Story 3 - Observe Health and Errors (Priority: P3)

As an operator, I want health and error responses to be consistent so I can monitor and troubleshoot the service.

**Why this priority**: Operational clarity reduces downtime and integration friction.

**Independent Test**: Can be fully tested by calling health endpoints and triggering known errors.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** I call a health endpoint, **Then** I receive a success response with version information.
2. **Given** a server-side error, **When** it occurs, **Then** I receive a consistent error response structure.

---

### Edge Cases

- What happens when MT5 is unavailable on the host?
- How are timeouts and long-running requests handled?
- What happens when authentication fails or tokens expire?
- How does the service handle empty responses from MT5?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST expose HTTP endpoints for MT5 data retrieval (account, symbols, ticks, rates, history).
- **FR-002**: The system MUST expose HTTP endpoints for trading operations with optional dry-run validation.
- **FR-003**: The system MUST provide request/response models with explicit validation errors.
- **FR-004**: The system MUST enforce authentication for all non-health endpoints.
- **FR-005**: The system MUST return consistent error responses with status codes and message details.
- **FR-006**: The system MUST provide a health or readiness endpoint for monitoring.
- **FR-007**: The system MUST include request formatting and response serialization rules that are stable for clients.

### Key Entities _(include if feature involves data)_

- **ApiRequest**: Represents validated API input for data or trading operations.
- **ApiResponse**: Represents structured API output for data or trade results.
- **AuthContext**: Represents authorization details for API access.
- **ErrorEnvelope**: Represents a standard error response structure.
- **HealthStatus**: Represents service readiness and version information.

## Dependencies

- [specs/041-mt5-rest-api/spec.md](specs/041-mt5-rest-api/spec.md)
- [specs/042-mt5-core-client/spec.md](specs/042-mt5-core-client/spec.md)
- [specs/043-mt5-dataframe-client/spec.md](specs/043-mt5-dataframe-client/spec.md)
- [specs/044-mt5-trading-client/spec.md](specs/044-mt5-trading-client/spec.md)
- [specs/045-mt5-utils/spec.md](specs/045-mt5-utils/spec.md)
- [specs/047-api-auth-rate-limit/spec.md](specs/047-api-auth-rate-limit/spec.md)
- [specs/048-api-response-format/spec.md](specs/048-api-response-format/spec.md)
- [specs/049-api-routing-models/spec.md](specs/049-api-routing-models/spec.md)
- [specs/050-api-runtime-deploy/spec.md](specs/050-api-runtime-deploy/spec.md)
- [specs/051-api-error-logging/spec.md](specs/051-api-error-logging/spec.md)
- [specs/052-api-dependencies/spec.md](specs/052-api-dependencies/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A client can retrieve MT5 data via HTTP and receive a valid JSON response.
- **SC-002**: Trading requests support dry-run validation with no execution side effects.
- **SC-003**: Unauthorized requests are consistently rejected with clear error responses.
- **SC-004**: Health endpoint returns a stable, versioned status payload.
