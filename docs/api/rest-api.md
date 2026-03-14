# REST API

The mt5api REST API exposes read-only MetaTrader 5 data via FastAPI. It supports
JSON and Apache Parquet responses for analytics workflows.

The API server must run on Windows because the `MetaTrader5` Python package is
supported only on Windows. Host `mt5api` on a Windows machine with MetaTrader 5
installed and logged in. HTTP clients can access the API from any operating
system.

## Runtime Requirements

- Python 3.11+
- Windows host with MetaTrader 5 terminal installed and logged in
- Linux and macOS are not supported for the API server runtime, but they work
  for HTTP clients

## Installation

Install the package on the Windows host that will run the API server.

```powershell
pip install mt5api
```

## Configuration

Set the optional API key and other limits via environment variables:

```powershell
$env:MT5_API_KEY = "your-secret-api-key"  # Optional: omit to disable auth
$env:API_LOG_LEVEL = "INFO"
$env:API_RATE_LIMIT = "100"
$env:API_CORS_ORIGINS = "*"
```

MT5 connection details are managed by `pdmt5` (for example login/server/path
settings defined in that package).

## Running the API

```powershell
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Access the docs at the Windows host address, for example:

- Swagger UI: `http://windows-host:8000/docs`
- OpenAPI JSON: `http://windows-host:8000/openapi.json`

Replace `windows-host` with the DNS name or IP address of the Windows machine
running `mt5api`. If you run the request on that Windows host, `localhost` also
works. In PowerShell, use `curl.exe` if `curl` resolves to
`Invoke-WebRequest`.

## Authentication

When `MT5_API_KEY` is set, all endpoints except `/api/v1/health` require an
`X-API-Key` header. When `MT5_API_KEY` is unset or empty, authentication is
disabled and those endpoints are accessible without authorization.

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/symbols"
```

## Rate Limiting

Rate limiting uses `slowapi` with a default limit of `100/minute`. Set
`API_RATE_LIMIT` to an integer for a different per-minute cap.

## Format Negotiation

Use `Accept` header or `format` query parameter:

```console
curl -H "X-API-Key: your-secret-api-key" -H "Accept: application/parquet" "http://windows-host:8000/api/v1/rates/from?symbol=EURUSD&timeframe=1&date_from=2024-01-01T00:00:00Z&count=100"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/symbols?format=json"
```

## Endpoints

All endpoints are read-only.

### Health

- `GET /api/v1/health` (no auth)
- `GET /api/v1/version`

### Symbols

- `GET /api/v1/symbols` (`group`, `format`)
- `GET /api/v1/symbols/{symbol}` (`format`)
- `GET /api/v1/symbols/{symbol}/tick` (`format`)

### Market Data

- `GET /api/v1/rates/from` (`symbol`, `timeframe`, `date_from`, `count`, `format`)
- `GET /api/v1/rates/from-pos` (`symbol`, `timeframe`, `start_pos`, `count`, `format`)
- `GET /api/v1/rates/range` (`symbol`, `timeframe`, `date_from`, `date_to`, `format`)
- `GET /api/v1/ticks/from` (`symbol`, `date_from`, `count`, `flags`, `format`)
- `GET /api/v1/ticks/range` (`symbol`, `date_from`, `date_to`, `flags`, `format`)
- `GET /api/v1/market-book/{symbol}` (`format`)

### Account & Trading State

- `GET /api/v1/account` (`format`)
- `GET /api/v1/terminal` (`format`)
- `GET /api/v1/positions` (`symbol`, `group`, `ticket`, `format`)
- `GET /api/v1/orders` (`symbol`, `group`, `ticket`, `format`)

### History

- `GET /api/v1/history/orders` (`date_from`, `date_to`, `ticket`, `position`, `group`, `symbol`, `format`)
- `GET /api/v1/history/deals` (`date_from`, `date_to`, `ticket`, `position`, `group`, `symbol`, `format`)

## Response Formatter Utilities

If you are extending the API with custom endpoints, use the formatter helpers
in `mt5api.formatters` to keep JSON and Parquet responses consistent:

- `format_response(data, response_format)`: Unified formatter for DataFrame or
  dict data.
- `format_dataframe_to_json(dataframe)`: Convert DataFrame to JSON response.
- `format_dataframe_to_parquet(dataframe)`: Convert DataFrame to Parquet
  response.
- `format_dict_to_json(data)`: Convert dict to JSON response.
- `format_dict_to_parquet(data)`: Convert dict to Parquet response.

## Example Requests

### Health Check (No Auth)

```console
curl "http://windows-host:8000/api/v1/health"
```

### MT5 Version

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/version"
```

### Symbols

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/symbols"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/symbols?group=*USD*"
```

### Symbol Details

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/symbols/EURUSD"
```

### Rates (OHLCV)

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/rates/from?symbol=EURUSD&timeframe=1&date_from=2024-01-01T00:00:00Z&count=100"
```

### Account Info

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/account"
```

### History Orders

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/history/orders?date_from=2024-01-01T00:00:00Z&date_to=2024-01-02T00:00:00Z"
```

## Error Responses

Errors follow RFC 7807 Problem Details:

```json
{
  "type": "/errors/validation-error",
  "title": "Request Validation Failed",
  "status": 400,
  "detail": "count must be positive (got: -10)",
  "instance": "/api/v1/rates/from"
}
```

## Security Checklist

Minimum security posture for deployments:

- Set `MT5_API_KEY` to enable API key authentication when needed
- Rate limiting enabled (`API_RATE_LIMIT`)
- Run behind HTTPS in production
- Restrict CORS origins (`API_CORS_ORIGINS`) for public deployments
