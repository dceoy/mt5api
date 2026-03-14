# mt5api Documentation

FastAPI-based REST API for MetaTrader 5 market data and account information.

## Overview

mt5api exposes read-only MT5 data over HTTP using FastAPI. It relies on the
`pdmt5` client for MT5 connectivity and adds optional authentication, rate
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
- Linux and macOS are not supported for the API server runtime

## Installation

Install `mt5api` on the Windows host that runs MetaTrader 5.

```powershell
pip install mt5api
```

## Quick Start

```powershell
$env:MT5_API_KEY = "your-secret-api-key"  # Optional: omit to disable auth
uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

```powershell
curl.exe http://localhost:8000/api/v1/health
```

```powershell
# Include X-API-Key only when MT5_API_KEY is configured on the server.
curl.exe -H "X-API-Key: your-secret-api-key" `
  "http://localhost:8000/api/v1/symbols?group=*USD*"
```

## API Reference

- [REST API](api/rest-api.md) - Endpoint overview, auth, and formats
- [Deployment](api/deployment.md) - Windows service setup
- [Mt5Client](api/mt5.md) - pdmt5 low-level MT5 client
- [Mt5DataClient & Mt5Config](api/dataframe.md) - pdmt5 DataFrame helpers
- [Mt5TradingClient](api/trading.md) - pdmt5 trading utilities
- [Utilities](api/utils.md) - pdmt5 decorators and helpers

## License

MIT License - see [LICENSE](https://github.com/dceoy/mt5api/blob/main/LICENSE).
