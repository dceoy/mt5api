# mt5api

MetaTrader 5 REST API

[![CI/CD](https://github.com/dceoy/mt5api/actions/workflows/ci.yml/badge.svg)](https://github.com/dceoy/mt5api/actions/workflows/ci.yml)

mt5api exposes MT5 market data, account info, trading history, and trading
operations over HTTP. It uses the [`pdmt5`](https://github.com/dceoy/pdmt5)
client internally and adds optional API-key auth, rate limiting, and
JSON/Parquet response formatting.

The API server must run on Windows. The `MetaTrader5` Python package used by
`pdmt5` is supported only on Windows, so you must host `mt5api` on a Windows
machine with a logged-in MetaTrader 5 terminal. HTTP clients can connect from
any operating system.

## Features

- REST endpoints for symbols, market data, account info, orders, history,
  calculations, and trading operations
- JSON and Apache Parquet responses (content negotiation)
- Optional API key authentication with per-minute rate limiting
- Structured JSON logging and configurable CORS
- OpenAPI/Swagger docs built into the API

## Requirements

- Python 3.11+
- Windows host with MetaTrader 5 terminal installed and logged in
- Linux and macOS are not supported for the API server runtime, but they work
  for HTTP clients

## Installation

Install and run the API on the Windows machine where MetaTrader 5 is installed.

```powershell
git clone https://github.com/dceoy/mt5api.git
cd mt5api
uv sync
```

## Running the API on Windows

```powershell
$env:MT5API_SECRET_KEY = "your-secret-api-key"  # Optional: omit to disable auth
$env:MT5API_ROUTER_PREFIX = "/api/v1"     # Optional: omit for root-level routes
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Docs:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Set `MT5API_ROUTER_PREFIX` to mount the API endpoints under a shared path such
as `/api/v1`. The default is `""`, which keeps routes like `/health` and
`/symbols` at the root. `"/api/v1"`, `"api/v1"`, and `"/api/v1/"` are treated
the same.

## Example Requests with curl

Replace `windows-host` with the DNS name or IP address of the Windows machine
running `mt5api`. If you run the request on that Windows host, `localhost` also
works. In PowerShell, use `curl.exe` if `curl` resolves to
`Invoke-WebRequest`.

```console
curl "http://windows-host:8000/health"
```

```console
# Include X-API-Key only when MT5API_SECRET_KEY is configured on the server.
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols?group=*USD*"
```

```console
curl -H "X-API-Key: your-secret-api-key" -H "Accept: application/parquet" "http://windows-host:8000/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_M1&date_from=2024-01-01T00:00:00Z&count=100"
```

Market-data and calculation endpoints accept MetaTrader 5 constants either by
official name (`TIMEFRAME_M1`, `COPY_TICKS_ALL`, `ORDER_TYPE_BUY`) or by their
integer value.

## Endpoints

If `MT5API_ROUTER_PREFIX` is set, prepend that value to every API route below.

### Read-Only Endpoints

- Health: `GET /health`, `GET /version`, `GET /last-error`
- Symbols: `GET /symbols`, `GET /symbols/total`, `GET /symbols/{symbol}`,
  `GET /symbols/{symbol}/tick`
- Market data: `GET /rates/from`, `GET /rates/from-pos`, `GET /rates/range`,
  `GET /ticks/from`, `GET /ticks/range`, `GET /market-book/{symbol}`
- Calculations: `GET /calc/margin`, `GET /calc/profit`
- Account: `GET /account`, `GET /terminal`
- Trading state: `GET /positions`, `GET /positions/total`,
  `GET /orders`, `GET /orders/total`
- History: `GET /history/orders`, `GET /history/orders/total`,
  `GET /history/deals`, `GET /history/deals/total`

### Operational Endpoints

- `POST /symbols/{symbol}/select` — Show or hide symbol in MarketWatch
- `POST /market-book/{symbol}/subscribe` — Subscribe to DOM events
- `POST /market-book/{symbol}/unsubscribe` — Unsubscribe from DOM events
- `POST /order/check` — Validate a trade request without execution

## License

MIT License - see [LICENSE](https://github.com/dceoy/mt5api/blob/main/LICENSE).
