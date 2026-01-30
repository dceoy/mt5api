# mt5api

MetaTrader 5 REST API using FastAPI

[![CI/CD](https://github.com/dceoy/mt5api/actions/workflows/ci.yml/badge.svg)](https://github.com/dceoy/mt5api/actions/workflows/ci.yml)

mt5api exposes read-only MT5 market data, account info, and trading history
over HTTP. It uses the `pdmt5` client internally and adds auth, rate limiting,
and JSON/Parquet response formatting.

## Features

- Read-only REST endpoints for symbols, market data, account info, orders, and history
- JSON and Apache Parquet responses (content negotiation)
- API key authentication with per-minute rate limiting
- Structured JSON logging and configurable CORS
- OpenAPI/Swagger docs built into the API

## Requirements

- Python 3.11+
- Windows host with MetaTrader 5 terminal installed and logged in

## Installation

```bash
$ git clone https://github.com/dceoy/mt5api.git
$ cd mt5api
$ uv sync
```

## Running the API

```bash
$ uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Docs:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Example Requests

```bash
$ curl http://localhost:8000/api/v1/health
```

```bash
$ curl -H "X-API-Key: your-secret-api-key" 'http://localhost:8000/api/v1/symbols?group=*USD*'
```

```bash
$ curl -H 'X-API-Key: your-secret-api-key' -H 'Accept: application/parquet' \
    'http://localhost:8000/api/v1/rates/from?symbol=EURUSD&timeframe=1&date_from=2024-01-01T00:00:00Z&count=100'
```

## Endpoints (Read-Only)

- Health: `/api/v1/health`, `/api/v1/version`
- Symbols: `/api/v1/symbols`, `/api/v1/symbols/{symbol}`, `/api/v1/symbols/{symbol}/tick`
- Market data: `/api/v1/rates/from`, `/api/v1/rates/from-pos`, `/api/v1/rates/range`,
  `/api/v1/ticks/from`, `/api/v1/ticks/range`, `/api/v1/market-book/{symbol}`
- Account: `/api/v1/account`, `/api/v1/terminal`
- Trading state: `/api/v1/positions`, `/api/v1/orders`
- History: `/api/v1/history/orders`, `/api/v1/history/deals`

## License

MIT License - see [LICENSE](https://github.com/dceoy/mt5api/blob/main/LICENSE).
