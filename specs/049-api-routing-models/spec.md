# Feature Specification: API Routing and Request Models

**Feature Branch**: `049-api-routing-models`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "API request validation models and routing for MT5 endpoints"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Call Typed MT5 Endpoints (Priority: P1)

As an API client, I want clear endpoints for market, symbol, account, and history data so I can retrieve MT5 data reliably.

**Why this priority**: Discoverable endpoints are the basis for any API integration.

**Independent Test**: Can be fully tested by calling each endpoint and validating HTTP status and response schema.

**Acceptance Scenarios**:

1. **Given** a valid request, **When** I call a market data endpoint, **Then** I receive a successful response with the expected data type.
2. **Given** a valid request, **When** I call account or history endpoints, **Then** I receive a structured response with consistent metadata.

---

### User Story 2 - Validate Requests with Clear Errors (Priority: P2)

As an API client, I want invalid requests rejected with clear validation errors so I can fix my inputs quickly.

**Why this priority**: Validation reduces misuse and clarifies requirements for integrators.

**Independent Test**: Can be fully tested by sending invalid payloads and confirming a 400 response with details.

**Acceptance Scenarios**:

1. **Given** missing or malformed parameters, **When** I call an endpoint, **Then** I receive a validation error describing the issue.
2. **Given** invalid date ranges, **When** I call a history endpoint, **Then** I receive a specific validation error.

---

### User Story 3 - Consistent Endpoint Groups (Priority: P3)

As a user, I want endpoints organized by domain (market, symbols, account, history, health) so I can navigate and document the API effectively.

**Why this priority**: Clear routing structure improves maintainability and documentation.

**Independent Test**: Can be fully tested by inspecting route registration and verifying grouped tags.

**Acceptance Scenarios**:

1. **Given** the API router configuration, **When** I list routes, **Then** endpoints are grouped by domain.
2. **Given** the OpenAPI schema, **When** I view the docs, **Then** the endpoints are categorized by tags.

---

### Edge Cases

- What happens when required parameters are missing?
- How are conflicting parameters (e.g., date range plus ticket) handled?
- What happens when the request payload is too large?
- How are unsupported formats or unknown query parameters handled?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST expose domain-specific routers for market, symbols, account, history, and health endpoints.
- **FR-002**: The system MUST validate request parameters using typed request models.
- **FR-003**: The system MUST reject invalid requests with a 400 response and a clear error message.
- **FR-004**: The system MUST enforce constraints such as positive counts, non-negative positions, and valid date ranges.
- **FR-005**: The system MUST provide consistent response metadata across endpoints.
- **FR-006**: The system MUST register endpoints with stable paths and tags for documentation.

### Key Entities _(include if feature involves data)_

- **RequestModel**: Represents typed and validated inputs for each endpoint.
- **RouteGroup**: Represents a domain grouping of API routes.
- **ValidationError**: Represents a standardized error returned on invalid input.

## Dependencies

- [specs/041-mt5-rest-api/spec.md](specs/041-mt5-rest-api/spec.md)
- [specs/046-mt5-api-service/spec.md](specs/046-mt5-api-service/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: All endpoints validate requests and return structured errors for invalid input.
- **SC-002**: OpenAPI schema groups routes by domain and includes model definitions.
- **SC-003**: Requests with valid parameters succeed without server-side validation errors.
