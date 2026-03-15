---
name: mt5-health
description: Check MT5 API health status and retrieve MT5 terminal version information. Use when verifying API availability, checking MT5 terminal connectivity, or retrieving version details.
allowed-tools: Bash
---

# MT5 Health & Version

Query the mt5api health check and version endpoints.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
When the server is configured with `MT5_API_KEY`, send the same value in the
`X-API-Key` header for protected endpoints. `/health` never requires
authentication.

## Response Formats

- `/health` always returns JSON.
- `/version` returns JSON by default and also supports
  `format=parquet` or `Accept: application/parquet`.

## Endpoints

### Health Check (public, no auth required)

```bash
curl -s "${MT5_API_URL:-http://localhost:8000}/health" | python -m json.tool
```

Returns:

| Field         | Type    | Description                    |
| ------------- | ------- | ------------------------------ |
| status        | string  | `healthy` or `unhealthy`       |
| mt5_connected | bool    | MT5 terminal connection status |
| mt5_version   | string? | MT5 terminal version string    |
| api_version   | string  | API version (e.g., `1.0.0`)    |

### MT5 Version (protected when auth is enabled)

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/version" | python -m json.tool
```

Returns a `DataResponse` with version data.

Example requesting Parquet:

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  -H "Accept: application/parquet" \
  "${MT5_API_URL:-http://localhost:8000}/version" > version.parquet
```

## Procedure

1. Determine which endpoint the user needs (health check or version).
2. Decide whether the caller needs JSON or Parquet output.
3. Run the appropriate `curl` command above.
4. Parse and summarize the JSON response for the user, or note when the
   endpoint returned Parquet data.
5. If the health status is `unhealthy`, note that the MT5 terminal may not be
   running or reachable.
