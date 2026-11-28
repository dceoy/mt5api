# API Reference

This section contains the public documentation for mt5api.

The API server must run on Windows because the `MetaTrader5` Python package is
Windows-only. Run `mt5api` on a Windows host with MetaTrader 5 installed and
logged in. Clients can call the HTTP API from any operating system.

## Guides

### [REST API](rest-api.md)

FastAPI-based REST API that exposes MT5 market data, account info, trading
history, calculations, and non-executing operational endpoints over HTTP with
JSON and Parquet support.

### [Deployment](deployment.md)

Windows service deployment guide for hosting the REST API alongside MetaTrader 5.

## Architecture Overview

mt5api provides a FastAPI layer on top of the MetaTrader 5 terminal runtime:

1. **API Layer** (`mt5api.main`, `mt5api.routers`): FastAPI app, routers, and
   response formatting. Routers are grouped by domain:
   - `health.py`: health check, version, last error
   - `symbols.py`: symbol listing, details, tick, and total
   - `market.py`: OHLCV rates, tick data, and market depth
   - `calc.py`: margin and profit calculations
   - `account.py`: account and terminal info
   - `history.py`: positions, orders, history with totals
   - `trading.py`: order check, symbol selection, market book subscriptions
2. **Dependency Layer** (`mt5api.dependencies`): MT5 client lifecycle and
   format negotiation
3. **Model Layer** (`mt5api.models`): Response schemas and MT5 constant
   metadata helpers (TIMEFRAME, COPY_TICKS, ORDER_TYPE)
4. **Formatter Layer** (`mt5api.formatters`): JSON and Parquet serialization
   helpers

## Usage Guidelines

- **Type Safety**: All endpoints and helpers include comprehensive type hints
- **Error Handling**: Centralized through RFC 7807 responses (see REST API docs)
- **Documentation**: Google-style docstrings with examples
- **Validation**: Pydantic models for requests and responses
- **Data Formats**: JSON and Parquet via content negotiation

## Quick Start

```powershell
$env:MT5API_SECRET_KEY = "your-secret-api-key"  # Required
$env:MT5API_ROUTER_PREFIX = "/api/v1"     # Optional: omit for root-level routes
uv run uvicorn mt5api.main:app --host 127.0.0.1 --port 8000
```

Optionally set `MT5API_MT5_PATH` for the default terminal and
`MT5API_MT5_TERMINALS` for comma-separated named `name=path` pairs. Requests
can select a name with `X-MT5-Terminal`; the active terminal is instance-global
and the last switch wins. See the [REST API guide](rest-api.md) for examples and
concurrency limitations.

Run this request on the Windows host with the configuration above. In
PowerShell, use `curl.exe` if `curl` resolves to
`Invoke-WebRequest`.

```console
# Include X-API-Key for protected endpoints.
curl -H "X-API-Key: your-secret-api-key" "http://localhost:8000/api/v1/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_M1&date_from=2024-01-01T00:00:00Z&count=100"
```

## Examples

See the [REST API](rest-api.md) guide for endpoint examples and request syntax.

The server requires a nonempty `MT5API_SECRET_KEY` and binds to `127.0.0.1`
by default. For remote access, explicitly set `MT5API_HOST` (or the uvicorn
`--host` option) and set `MT5API_TRUSTED_HOSTS` to a comma-separated list of
allowed Host names or IP addresses, such as `windows-host,localhost,127.0.0.1`.
The default allowlist is `localhost,127.0.0.1,[::1]`.
