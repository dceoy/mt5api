# REST API

The mt5api REST API exposes MetaTrader 5 data and trading operations via
FastAPI. It supports JSON and Apache Parquet responses for analytics workflows.

The API server must run on Windows because the `MetaTrader5` Python package is
supported only on Windows. Host `mt5api` on a Windows machine with MetaTrader 5
installed and logged in. HTTP clients can access the API from any operating
system.

## Runtime Requirements

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
$env:MT5API_SECRET_KEY = "your-secret-api-key"  # Optional: omit to disable auth
$env:MT5API_LOG_LEVEL = "INFO"
$env:MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS = "100"
$env:MT5API_ROUTER_PREFIX = "/api/v1"     # Optional: omit for root-level routes
```

MT5 connection details are managed by the underlying MT5 client configuration
(for example login/server/path settings).

`MT5API_ROUTER_PREFIX` mounts the API routers under a shared prefix such as
`/api/v1`. The default is `""`, so endpoints stay at root-level paths like
`/health` and `/symbols`. `"api/v1"`, `"/api/v1"`, and `"/api/v1/"` are
normalized to the same prefix.

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

When `MT5API_SECRET_KEY` is set, all endpoints except `/health` require an
`X-API-Key` header. When `MT5API_SECRET_KEY` is unset or empty, authentication is
disabled and those endpoints are accessible without authorization.

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols"
```

## Subscription Limits

Active market-book subscriptions are capped at `100` symbols by default. Set
`MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS` to a positive integer to adjust that
limit. When the cap is reached, new `POST /market-book/{symbol}/subscribe`
requests return HTTP `429` until an existing subscription is released.

## Format Negotiation

Use `Accept` header or `format` query parameter:

```console
curl -H "X-API-Key: your-secret-api-key" -H "Accept: application/parquet" "http://windows-host:8000/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_M1&date_from=2024-01-01T00:00:00Z&count=100"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols?format=json"
```

## Endpoints

If `MT5API_ROUTER_PREFIX` is configured, prepend it to each API route below.

### Health

- `GET /health` (no auth) — API and MT5 connection status
- `GET /version` — MT5 terminal version
- `GET /last-error` — Last MT5 error code and description

### Symbols

- `GET /symbols` (`group`, `format`) — List available symbols
- `GET /symbols/total` (`format`) — Total number of symbols
- `GET /symbols/{symbol}` (`format`) — Symbol details
- `GET /symbols/{symbol}/tick` (`format`) — Latest tick for a symbol
- `POST /symbols/{symbol}/select` (`enable`) — Show or hide a symbol in
  MarketWatch

### Market Data

- `timeframe` and `flags` accept the official MetaTrader 5 constant name (for
  example `TIMEFRAME_M1`, `COPY_TICKS_ALL`), a short alias (for example `M1`,
  `ALL`), or the equivalent integer value.
- `GET /rates/from` (`symbol`, `timeframe`, `date_from`, `count`, `format`)
- `GET /rates/from-pos` (`symbol`, `timeframe`, `start_pos`, `count`, `format`)
- `GET /rates/range` (`symbol`, `timeframe`, `date_from`, `date_to`, `format`)
- `GET /ticks/from` (`symbol`, `date_from`, `count`, `flags`, `format`)
- `GET /ticks/range` (`symbol`, `date_from`, `date_to`, `flags`, `format`)
- `GET /market-book/{symbol}` (`format`) — Market depth (DOM) _(experimental)_
- `POST /market-book/{symbol}/subscribe` — Subscribe to DOM events _(experimental)_
- `POST /market-book/{symbol}/unsubscribe` — Unsubscribe from DOM events _(experimental)_

### Calculations

- `action` accepts the official MetaTrader 5 constant name (for example
  `ORDER_TYPE_BUY`), a short alias (for example `BUY`), or the equivalent
  integer value.
- `GET /calc/margin` (`action`, `symbol`, `volume`, `price`, `format`) —
  Calculate required margin in account currency
- `GET /calc/profit` (`action`, `symbol`, `volume`, `price_open`,
  `price_close`, `format`) — Calculate expected profit in account currency

### Account & Terminal

- `GET /account` (`format`) — Account balance, equity, margin
- `GET /terminal` (`format`) — Terminal status and settings

### Positions & Orders

- `GET /positions` (`symbol`, `group`, `ticket`, `format`) — Open positions
- `GET /positions/total` (`format`) — Count of open positions
- `GET /orders` (`symbol`, `group`, `ticket`, `format`) — Active pending orders
- `GET /orders/total` (`format`) — Count of active orders

### History

- `GET /history/orders` (`date_from`, `date_to`, `ticket`, `position`, `group`, `symbol`, `format`)
- `GET /history/orders/total` (`date_from`, `date_to`, `format`) — Count of
  historical orders in date range
- `GET /history/deals` (`date_from`, `date_to`, `ticket`, `position`, `group`, `symbol`, `format`)
- `GET /history/deals/total` (`date_from`, `date_to`, `format`) — Count of
  historical deals in date range

### Trade Validation

This endpoint validates an MT5 trade request without executing it.

- `POST /order/check` (body: `{"request": {...}}`) — Validate funds
  sufficiency for a trade without executing it

The `request` body follows the [MetaTrader 5 trade request
structure](https://www.mql5.com/en/docs/constants/structures/mqltraderequest),
with typed validation for core fields such as `action`, `symbol`, `volume`,
`type`, and `price`.

### Connection

- `POST /connection/login` (body: `{"login": ..., "password": "...",
  "server": "...", "timeout": ...}`) — Reconnect the MT5 terminal with the
  supplied credentials. The replacement client is initialized and installed
  before active market-book subscriptions are released and cleared. The old
  wrapper is not shut down after a successful replacement because MetaTrader5
  connection state is process-global; shutting it down could close the newly
  established session. If replacement fails, existing subscription tracking is
  preserved. The supplied password is never echoed in responses or logs.

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
curl "http://windows-host:8000/health"
```

### MT5 Version

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/version"
```

### Last Error

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/last-error"
```

### Symbols

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols?group=*USD*"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols/total"
```

### Symbol Details

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols/EURUSD"
```

### Select Symbol in MarketWatch

```console
curl -X POST -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols/EURUSD/select?enable=true"
```

### Rates (OHLCV)

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_M1&date_from=2024-01-01T00:00:00Z&count=100"
```

### Market Depth

```console
curl -X POST -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/market-book/EURUSD/subscribe"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/market-book/EURUSD"
```

```console
curl -X POST -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/market-book/EURUSD/unsubscribe"
```

### Calculate Margin

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/calc/margin?action=ORDER_TYPE_BUY&symbol=EURUSD&volume=0.1&price=1.08500"
```

### Calculate Profit

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/calc/profit?action=ORDER_TYPE_BUY&symbol=EURUSD&volume=0.1&price_open=1.08500&price_close=1.09000"
```

### Account Info

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/account"
```

### Positions & Orders

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/positions"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/positions/total"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/orders/total"
```

### History Orders

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/history/orders?date_from=2024-01-01T00:00:00Z&date_to=2024-01-02T00:00:00Z"
```

```console
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/history/orders/total?date_from=2024-01-01T00:00:00Z&date_to=2024-01-02T00:00:00Z"
```

### Check Order Funds

```console
curl -X POST -H "X-API-Key: your-secret-api-key" -H "Content-Type: application/json" \
  -d '{"request": {"action": 1, "symbol": "EURUSD", "volume": 0.1, "type": 0, "price": 1.085}}' \
  "http://windows-host:8000/order/check"
```

### Reconnect to MT5

```console
curl -X POST -H "X-API-Key: your-secret-api-key" -H "Content-Type: application/json" \
  -d '{"login": 12345678, "password": "s3cret", "server": "MetaQuotes-Demo", "timeout": 60000}' \
  "http://windows-host:8000/connection/login"
```

## Error Responses

Errors follow RFC 7807 Problem Details:

```json
{
  "type": "/errors/validation-error",
  "title": "Request Validation Failed",
  "status": 422,
  "detail": "Request validation error details",
  "instance": "/rates/from"
}
```

## Security Checklist

Minimum security posture for deployments:

- Set `MT5API_SECRET_KEY` to enable API key authentication when needed
- Configure rate limiting at the reverse proxy or API gateway level
- Run behind HTTPS in production
- Restrict access to operational endpoints (`/order/check`,
  `/symbols/{symbol}/select`, `/market-book/{symbol}/subscribe`,
  `/market-book/{symbol}/unsubscribe`) to trusted clients only
