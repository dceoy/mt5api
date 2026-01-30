# REST API

The mt5api REST API exposes read-only MetaTrader 5 data via FastAPI. It supports
JSON and Apache Parquet responses for analytics workflows.

## Installation

```bash
pip install mt5api
```

## Configuration

Set the API key and optional limits via environment variables:

```bash
export MT5_API_KEY="your-secret-api-key"
export API_LOG_LEVEL="INFO"
export API_RATE_LIMIT="100"
export API_CORS_ORIGINS="*"
```

MT5 connection details are managed by `pdmt5` (for example login/server/path
settings defined in that package).

## Running the API

```bash
uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Access the docs at:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Authentication

All endpoints except `/api/v1/health` require an API key header:

```bash
curl -H "X-API-Key: your-secret-api-key" \
  http://localhost:8000/api/v1/symbols
```

## Rate Limiting

Rate limiting uses `slowapi` with a default limit of `100/minute`. Set
`API_RATE_LIMIT` to an integer for a different per-minute cap.

## Format Negotiation

Use `Accept` header or `format` query parameter:

```bash
curl -H "X-API-Key: your-secret-api-key" \
  -H "Accept: application/parquet" \
  "http://localhost:8000/api/v1/rates/from?symbol=EURUSD&timeframe=1&date_from=2024-01-01T00:00:00Z&count=100"
```

```bash
curl -H "X-API-Key: your-secret-api-key" \
  "http://localhost:8000/api/v1/symbols?format=json"
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

```bash
curl http://localhost:8000/api/v1/health
```

### MT5 Version

```bash
curl -H "X-API-Key: your-secret-api-key" \
  http://localhost:8000/api/v1/version
```

### Symbols

```bash
curl -H "X-API-Key: your-secret-api-key" \
  http://localhost:8000/api/v1/symbols
```

```bash
curl -H "X-API-Key: your-secret-api-key" \
  "http://localhost:8000/api/v1/symbols?group=*USD*"
```

### Symbol Details

```bash
curl -H "X-API-Key: your-secret-api-key" \
  http://localhost:8000/api/v1/symbols/EURUSD
```

### Rates (OHLCV)

```bash
curl -H "X-API-Key: your-secret-api-key" \
  "http://localhost:8000/api/v1/rates/from?symbol=EURUSD&timeframe=1&date_from=2024-01-01T00:00:00Z&count=100"
```

### Account Info

```bash
curl -H "X-API-Key: your-secret-api-key" \
  http://localhost:8000/api/v1/account
```

### History Orders

```bash
curl -H "X-API-Key: your-secret-api-key" \
  "http://localhost:8000/api/v1/history/orders?date_from=2024-01-01T00:00:00Z&date_to=2024-01-02T00:00:00Z"
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

- API key authentication enabled (`MT5_API_KEY`)
- Rate limiting enabled (`API_RATE_LIMIT`)
- Run behind HTTPS in production
- Restrict CORS origins (`API_CORS_ORIGINS`) for public deployments
