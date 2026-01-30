# mt5api Documentation

FastAPI-based REST API for MetaTrader 5 market data and account information.

## Overview

mt5api exposes read-only MT5 data over HTTP using FastAPI. It relies on the
`pdmt5` client for MT5 connectivity and adds authentication, rate limiting,
and response formatting suitable for analytics workflows.

## Features

- Read-only REST endpoints for symbols, market data, account info, orders, and history
- JSON and Apache Parquet responses
- API key authentication and rate limiting
- Structured JSON logging and configurable CORS
- OpenAPI/Swagger docs built in

## Requirements

- Python 3.11+
- Windows OS with MetaTrader 5 terminal installed and logged in

## Installation

```bash
pip install mt5api
```

## Quick Start

```bash
export MT5_API_KEY="your-secret-api-key"
uvicorn mt5api.main:app --host 0.0.0.0 --port 8000
```

```bash
curl http://localhost:8000/api/v1/health
```

```bash
curl -H "X-API-Key: your-secret-api-key" \
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
