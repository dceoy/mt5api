# API Reference

This section contains the public documentation for mt5api.

The API server must run on Windows because the `MetaTrader5` Python package is
Windows-only. Run `mt5api` on a Windows host with MetaTrader 5 installed and
logged in. Clients can call the HTTP API from any operating system.

## Guides

### [REST API](rest-api.md)

FastAPI-based REST API that exposes read-only MT5 data over HTTP with JSON and
Parquet support.

### [Deployment](deployment.md)

Windows service deployment guide for hosting the REST API alongside MetaTrader 5.

## Architecture Overview

mt5api provides a FastAPI layer on top of the MetaTrader 5 terminal runtime:

1. **API Layer** (`mt5api.main`, `mt5api.routers`): FastAPI app, routers, and response formatting
2. **Dependency Layer** (`mt5api.dependencies`): MT5 client lifecycle and format negotiation
3. **Model Layer** (`mt5api.models`): Response schemas and MT5 constant metadata helpers
4. **Formatter Layer** (`mt5api.formatters`): JSON and Parquet serialization helpers

## Usage Guidelines

- **Type Safety**: All endpoints and helpers include comprehensive type hints
- **Error Handling**: Centralized through RFC 7807 responses (see REST API docs)
- **Documentation**: Google-style docstrings with examples
- **Validation**: Pydantic models for requests and responses
- **Data Formats**: JSON and Parquet via content negotiation

## Quick Start

```powershell
$env:MT5_API_KEY = "your-secret-api-key"  # Optional: omit to disable auth
$env:API_ROUTER_PREFIX = "/api/v1"        # Optional: omit for root-level routes
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Replace `windows-host` with the DNS name or IP address of the Windows machine
running `mt5api`. If you run the request on that Windows host, `localhost` also
works. In PowerShell, use `curl.exe` if `curl` resolves to
`Invoke-WebRequest`.

```console
# Include X-API-Key only when MT5_API_KEY is configured on the server.
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_M1&date_from=2024-01-01T00:00:00Z&count=100"
```

## Examples

See the [REST API](rest-api.md) guide for endpoint examples and request syntax.
