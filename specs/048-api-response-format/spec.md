# Feature Specification: API Response Formatting

**Feature Branch**: `048-api-response-format`  
**Created**: 2026-01-09  
**Status**: Implemented  
**Implementation**: Existing code  
**Input**: User description: "API response formatting and data serialization"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Receive JSON Responses by Default (Priority: P1)

As an API client, I want JSON responses by default so I can consume MT5 data in a standard format.

**Why this priority**: JSON is the most broadly supported response format for API clients.

**Independent Test**: Can be fully tested by calling data endpoints and validating JSON structure and count metadata.

**Acceptance Scenarios**:

1. **Given** a data endpoint request, **When** I do not specify a format, **Then** I receive JSON data with a record count.
2. **Given** a single-record endpoint, **When** I request data, **Then** I receive a JSON object with count set appropriately.

---

### User Story 2 - Download Parquet for Analytics (Priority: P2)

As a data engineer, I want to request Parquet responses so I can efficiently ingest MT5 data into analytical pipelines.

**Why this priority**: Parquet is efficient for large datasets and columnar analytics workflows.

**Independent Test**: Can be fully tested by requesting Parquet output and verifying the response is a valid Parquet file.

**Acceptance Scenarios**:

1. **Given** a data endpoint request with format=parquet, **When** I call the endpoint, **Then** I receive a Parquet binary response.
2. **Given** a dict response, **When** I request Parquet, **Then** the service returns a single-row Parquet file.

---

### User Story 3 - Consistent Response Metadata (Priority: P3)

As an API client, I want consistent response metadata (count and format) so I can build predictable clients.

**Why this priority**: Stable metadata improves client interoperability and reduces conditional logic.

**Independent Test**: Can be fully tested by comparing metadata across multiple endpoints and formats.

**Acceptance Scenarios**:

1. **Given** JSON responses, **When** I call different endpoints, **Then** the response includes data, count, and format fields.
2. **Given** empty datasets, **When** I call a data endpoint, **Then** the response includes count=0 and an empty data structure.

---

### Edge Cases

- What happens when a DataFrame includes complex dtypes that are not serializable to JSON?
- How are empty DataFrames represented in Parquet responses?
- What happens when the response format is unsupported?
- How does the service handle very large datasets?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST return JSON responses by default for data endpoints.
- **FR-002**: The system MUST support Parquet responses for DataFrame-based endpoints.
- **FR-003**: The system MUST include a record count in JSON responses.
- **FR-004**: The system MUST include the response format indicator in JSON responses.
- **FR-005**: The system MUST return a valid Parquet response with appropriate content type.
- **FR-006**: The system MUST support serializing both DataFrame and dict outputs.
- **FR-007**: The system MUST return a clear error response for unsupported response formats.

### Key Entities _(include if feature involves data)_

- **ResponseFormat**: Represents the output format requested by clients.
- **DataResponse**: Represents JSON response metadata and payload.
- **ParquetResponse**: Represents a binary Parquet response for tabular data.
- **SerializedPayload**: Represents the serialized form of DataFrame or dict outputs.

## Dependencies

- [specs/041-mt5-rest-api/spec.md](specs/041-mt5-rest-api/spec.md)
- [specs/046-mt5-api-service/spec.md](specs/046-mt5-api-service/spec.md)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: JSON responses include data, count, and format fields for all data endpoints.
- **SC-002**: Parquet responses are valid and can be read by standard Parquet tools.
- **SC-003**: Unsupported format requests return a clear, consistent error response.
