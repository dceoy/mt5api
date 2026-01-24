# Feature Specification: API Authentication and Rate Limiting

**Feature Branch**: `047-api-auth-rate-limit`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "API authentication and rate limiting for REST endpoints"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Authenticate API Requests (Priority: P1)

As an API operator, I want all non-health endpoints protected by an API key so only authorized clients can access MT5 data and trading functionality.

**Why this priority**: Unauthenticated access to market data and trading operations is a security risk.

**Independent Test**: Can be fully tested by calling a protected endpoint with and without the API key and verifying the responses.

**Acceptance Scenarios**:

1. **Given** the API key is configured, **When** I call a protected endpoint with a valid key, **Then** the request succeeds.
2. **Given** the API key is configured, **When** I call a protected endpoint with a missing or invalid key, **Then** I receive a 401 error response.

---

### User Story 2 - Operate Safely Without Secrets in Code (Priority: P2)

As an operator, I want the API key loaded from the environment so I can manage secrets outside the codebase.

**Why this priority**: Environment-based secrets are standard for secure deployment.

**Independent Test**: Can be fully tested by launching the service with and without the environment variable set.

**Acceptance Scenarios**:

1. **Given** the environment variable is set, **When** the API starts, **Then** authentication works without code changes.
2. **Given** the environment variable is missing, **When** a protected endpoint is called, **Then** a clear runtime error is returned.

---

### User Story 3 - Prevent Abuse with Rate Limits (Priority: P3)

As an operator, I want rate limiting applied per client so the service remains stable under load and misuse.

**Why this priority**: Rate limiting protects MT5 resources and API availability.

**Independent Test**: Can be fully tested by exceeding the configured request rate and verifying the error response.

**Acceptance Scenarios**:

1. **Given** a configured rate limit, **When** a client exceeds the limit, **Then** the API returns a 429 response.
2. **Given** normal usage below the limit, **When** requests are made, **Then** they proceed without throttling.

---

### Edge Cases

- What happens when the API key environment variable is missing?
- How are rate limits applied to localhost or internal traffic?
- What happens when the client IP cannot be determined?
- How do authentication errors appear in the standardized error format?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST require an API key for all non-health endpoints.
- **FR-002**: The system MUST read the API key from an environment variable.
- **FR-003**: The system MUST return a 401 response for missing or invalid API keys.
- **FR-004**: The system MUST apply rate limits per client identity (e.g., remote address).
- **FR-005**: The system MUST return a 429 response when rate limits are exceeded.
- **FR-006**: The system MUST expose configurable rate limits via environment settings.
- **FR-007**: The system MUST return error responses in a consistent problem-details structure.

### Key Entities _(include if feature involves data)_

- **ApiKey**: Represents the configured API secret used for authentication.
- **AuthDecision**: Represents the outcome of authentication checks.
- **RateLimitPolicy**: Represents per-client request limits.
- **ErrorEnvelope**: Represents the standardized error response structure.

## Dependencies

- [specs/041-mt5-rest-api/spec.md](specs/041-mt5-rest-api/spec.md)
- [specs/046-mt5-api-service/spec.md](specs/046-mt5-api-service/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Protected endpoints reject requests without a valid API key.
- **SC-002**: Rate limit violations return a 429 response with a clear error message.
- **SC-003**: Authentication configuration can be changed without code changes.
