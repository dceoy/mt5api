---
name: mt5-health
description: Check MT5 API health status and retrieve MT5 terminal version information. Use when verifying API availability, checking MT5 terminal connectivity, or retrieving version details.
allowed-tools: Bash
---

# MT5 Health & Version

Query the mt5api health check and version endpoints.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
Authenticated endpoints require the `X-API-Key` header. Set `MT5_API_KEY` in the environment.

## Endpoints

### Health Check (public, no auth required)

```bash
curl -s "${MT5_API_URL:-http://localhost:8000}/api/v1/health" | python -m json.tool
```

Returns:

| Field         | Type    | Description                    |
| ------------- | ------- | ------------------------------ |
| status        | string  | `healthy` or `unhealthy`       |
| mt5_connected | bool    | MT5 terminal connection status |
| mt5_version   | string? | MT5 terminal version string    |
| api_version   | string  | API version (e.g., `1.0.0`)    |

### MT5 Version (requires API key)

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/api/v1/version" | python -m json.tool
```

Returns a `DataResponse` with version data.

## Procedure

1. Determine which endpoint the user needs (health check or version).
2. Run the appropriate `curl` command above.
3. Parse and summarize the JSON response for the user.
4. If the health status is `unhealthy`, note that the MT5 terminal may not be running or reachable.
