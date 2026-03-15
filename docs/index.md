# mt5api Documentation

FastAPI-based REST API for MetaTrader 5 market data and account information.

## Overview

mt5api exposes read-only MT5 data over HTTP using FastAPI. It relies on the
underlying MT5 client library for connectivity and adds optional authentication, rate
limiting, and response formatting suitable for analytics workflows.

The API server must run on Windows because the `MetaTrader5` Python package is
Windows-only. Run `mt5api` on a Windows host with MetaTrader 5 installed and
logged in. API clients can connect from any operating system.

## Features

- Read-only REST endpoints for symbols, market data, account info, orders, and history
- JSON and Apache Parquet responses
- Optional API key authentication and rate limiting
- Structured JSON logging and configurable CORS
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
$env:MT5_API_KEY = "your-secret-api-key"  # Optional: omit to disable auth
$env:API_ROUTER_PREFIX = "/api/v1"        # Optional: omit for root-level routes
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Once the API is running, use these `curl` examples from any client machine.

Replace `windows-host` with the DNS name or IP address of the Windows machine
running `mt5api`. If you run the request on that Windows host, `localhost` also
works. In PowerShell, use `curl.exe` if `curl` resolves to
`Invoke-WebRequest`.

```console
curl "http://windows-host:8000/health"
```

```console
# Include X-API-Key only when MT5_API_KEY is configured on the server.
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/symbols?group=*USD*"
```

## API Reference

- [REST API](api/rest-api.md) - Endpoint overview, auth, and formats
- [Deployment](api/deployment.md) - Windows service setup

## License

MIT License - see [LICENSE](https://github.com/dceoy/mt5api/blob/main/LICENSE).
