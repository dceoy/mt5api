# mt5api Documentation

FastAPI-based REST API for MetaTrader 5 market data, account information, and
trading operations.

## Overview

mt5api is a FastAPI/HTTP adapter over
[`pdmt5`](https://github.com/dceoy/pdmt5). pdmt5 provides the core MT5 client,
dataframe/trading primitives, and canonical MT5 constant parsing. mt5api adds
API-key authentication, response formatting, and OpenAPI documentation.

The API server must run on Windows because pdmt5 connects through the MetaTrader
5 Python API, which is Windows-only. Run `mt5api` on a Windows host with
MetaTrader 5 installed and logged in. API clients can connect from any operating
system.

## Features

- REST endpoints for symbols, market data, account info, orders, history,
  calculations, and trading operations
- JSON and Apache Parquet responses
- Required API key authentication
- Structured JSON logging
- OpenAPI/Swagger docs built in

## Requirements

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
$env:MT5API_SECRET_KEY = "your-secret-api-key"  # Required
$env:MT5API_ROUTER_PREFIX = "/api/v1"     # Optional: omit for root-level routes
uv run uvicorn mt5api.main:app --host 127.0.0.1 --port 8000
```

Once the API is running, use these `curl` examples on the Windows host.

Set `MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS` to cap active market-book
subscriptions. The default limit is `100`.

In PowerShell, use `curl.exe` if `curl` resolves to `Invoke-WebRequest`.

```console
curl "http://localhost:8000/api/v1/health"
```

```console
# Include X-API-Key for protected endpoints.
curl -H "X-API-Key: your-secret-api-key" "http://localhost:8000/api/v1/symbols?group=*USD*"
```

For remote clients, set the allowlist to the actual DNS name or IP they use,
and bind the server to an accessible interface:

```powershell
$env:MT5API_TRUSTED_HOSTS = "windows-host,localhost,127.0.0.1"
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Remote clients can then use `http://windows-host:8000/api/v1/health`.

## API Reference

- [REST API](api/rest-api.md) - Endpoint overview, auth, formats, and examples
- [Deployment](api/deployment.md) - Windows service setup

## License

MIT License - see [LICENSE](https://github.com/dceoy/mt5api/blob/main/LICENSE).

The server requires a nonempty `MT5API_SECRET_KEY` and binds to `127.0.0.1`
by default. For remote access, explicitly set `MT5API_HOST` (or the uvicorn
`--host` option) and set `MT5API_TRUSTED_HOSTS` to a comma-separated list of
allowed Host names or IP addresses, such as `windows-host,localhost,127.0.0.1`.
The default allowlist is `localhost,127.0.0.1,[::1]`.

A whitespace-only key is missing; leading or trailing spaces in any other key
are preserved. Documentation endpoints require `X-API-Key` on every request,
including the schema fetch. For browser access, use a trusted proxy that adds
the header to those requests.
