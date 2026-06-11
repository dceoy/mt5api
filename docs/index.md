# mt5api Documentation

FastAPI-based REST API for MetaTrader 5 market data, account information, and
trading operations.

## Overview

mt5api is a FastAPI/HTTP adapter over
[`pdmt5`](https://github.com/dceoy/pdmt5). pdmt5 provides the core MT5 client,
dataframe/trading primitives, and canonical MT5 constant parsing. mt5api adds
optional authentication, response formatting, and OpenAPI documentation.

[`mt5cli`](https://github.com/dceoy/mt5cli) is a sibling CLI/batch adapter for
the same pdmt5 stack; it is not a dependency of mt5api.

The API server must run on Windows because pdmt5 connects through the MetaTrader
5 Python API, which is Windows-only. Run `mt5api` on a Windows host with
MetaTrader 5 installed and logged in. API clients can connect from any operating
system.

## Features

- REST endpoints for symbols, market data, account info, orders, history,
  calculations, and trading operations
- JSON and Apache Parquet responses
- Optional API key authentication
- Structured JSON logging
- OpenAPI/Swagger docs built in

## Requirements

- Python 3.11+
- Windows OS with MetaTrader 5 terminal installed and logged in
- Linux and macOS are not supported for the API server runtime, but they work
  for HTTP clients

## Installation

Install `mt5api` on the Windows host that runs MetaTrader 5.

```powershell
pip install mt5api
```

## Quick Start

```powershell
$env:MT5API_SECRET_KEY = "your-secret-api-key"  # Optional: omit to disable auth
$env:MT5API_ROUTER_PREFIX = "/api/v1"     # Optional: omit for root-level routes
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Once the API is running, use these `curl` examples from any client machine.

Set `MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS` to cap active market-book
subscriptions. The default limit is `100`.

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

## API Reference

- [REST API](api/rest-api.md) - Endpoint overview, auth, formats, and examples
- [Deployment](api/deployment.md) - Windows service setup

## License

MIT License - see [LICENSE](https://github.com/dceoy/mt5api/blob/main/LICENSE).
