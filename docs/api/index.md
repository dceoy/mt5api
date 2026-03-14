# API Reference

This section contains the API documentation for mt5api and the underlying
`pdmt5` client modules.

The API server must run on Windows because the `MetaTrader5` Python package is
Windows-only. Run `mt5api` on a Windows host with MetaTrader 5 installed and
logged in. Clients can call the HTTP API from any operating system.

## Modules

### [REST API](rest-api.md)

FastAPI-based REST API that exposes read-only MT5 data over HTTP with JSON and
Parquet support.

### [Deployment](deployment.md)

Windows service deployment guide for hosting the REST API alongside MetaTrader 5.

### [Mt5Client](mt5.md)

Base client class for MetaTrader 5 operations with connection management, low-level
API access, and error handling (`Mt5RuntimeError`).

### [Mt5DataClient & Mt5Config](dataframe.md)

Core data client functionality and configuration, providing pandas-friendly interface
to MetaTrader 5.

### [Mt5TradingClient](trading.md)

Advanced trading operations including position management, order analysis, and
trading performance metrics with dry run support.

### [Utilities](utils.md)

Helper functions for time conversion and DataFrame manipulation.

## Architecture Overview

mt5api adds a FastAPI layer on top of pdmt5:

1. **API Layer** (`mt5api.main`, `mt5api.routers`): FastAPI app, routers, and response formatting
2. **Dependency Layer** (`mt5api.dependencies`): MT5 singleton client and format negotiation
3. **Base Layer** (`pdmt5.mt5`): Low-level MT5 API access and `Mt5RuntimeError`
4. **Data Layer** (`pdmt5.dataframe`): DataFrame conversion and configuration (`Mt5Config`)
5. **Trading Layer** (`pdmt5.trading`): Trading utilities and `Mt5TradingError`
6. **Utilities** (`pdmt5.utils`): Time conversion and DataFrame helpers

## Usage Guidelines

- **Type Safety**: All endpoints and helpers include comprehensive type hints
- **Error Handling**: Centralized through RFC 7807 responses (see REST API docs)
- **Documentation**: Google-style docstrings with examples
- **Validation**: Pydantic models for requests and responses
- **Data Formats**: JSON and Parquet via content negotiation

## Quick Start

```powershell
$env:MT5_API_KEY = "your-secret-api-key"  # Optional: omit to disable auth
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

Replace `windows-host` with the DNS name or IP address of the Windows machine
running `mt5api`. If you run the request on that Windows host, `localhost` also
works. In PowerShell, use `curl.exe` if `curl` resolves to
`Invoke-WebRequest`.

```console
# Include X-API-Key only when MT5_API_KEY is configured on the server.
curl -H "X-API-Key: your-secret-api-key" "http://windows-host:8000/api/v1/rates/from?symbol=EURUSD&timeframe=1&date_from=2024-01-01T00:00:00Z&count=100"
```

## Examples

See individual module pages for detailed usage examples and code samples.
