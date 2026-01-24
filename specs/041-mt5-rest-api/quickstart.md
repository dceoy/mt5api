# Quickstart Guide: MT5 REST API

**Feature**: REST API for MetaTrader 5 Data Access
**Branch**: `041-mt5-rest-api`
**Date**: 2026-01-02

## Overview

The MT5 REST API provides HTTP access to MetaTrader 5 market data, account information, and trading history. This guide covers installation, configuration, and usage examples.

## Prerequisites

- **Windows 10/11**: Required (MetaTrader5 API limitation)
- **MetaTrader 5**: Installed and configured
- **Python 3.11+**: Matching pdmt5 requirements
- **MT5 Account**: Demo or live account configured in MT5 terminal

## Installation

### Option 1: Install with API extras (recommended)

```bash
# Install pdmt5 with API dependencies
pip install pdmt5[api]
```

### Option 2: Development installation

```bash
# Clone repository
git clone https://github.com/dceoy/pdmt5.git
cd pdmt5

# Install with development dependencies
uv sync --extra api

# Or with pip
pip install -e ".[api]"
```

### Dependencies installed

The `[api]` extra installs:

- FastAPI 0.109+
- uvicorn[standard]
- pyarrow (Parquet support)
- python-jose[cryptography] (JWT authentication)
- passlib[bcrypt] (password hashing)
- python-multipart
- httpx (for testing)

## Configuration

### Environment Variables

Create a `.env` file in your working directory:

```bash
# MT5 Connection (optional if already configured in terminal)
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Demo
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MT5_API_KEY=your-secret-api-key-here  # Change this!
API_LOG_LEVEL=INFO

# Optional: Rate limiting
API_RATE_LIMIT=100  # requests per minute

# Optional: CORS
API_CORS_ORIGINS=*
```

### Generate API Key

```python
# Generate a secure API key
import secrets
api_key = secrets.token_urlsafe(32)
print(f"MT5_API_KEY={api_key}")
```

Output: `API_KEY=xK9vP2mN8hQ5wR7tY4uI0oL3jF6gH1sA2zX`

## Running the API

### Method 1: Using uvicorn directly

```bash
# Start the API server
uvicorn pdmt5.api.main:app --host 0.0.0.0 --port 8000
```

### Method 2: Using Python module

```bash
python -m pdmt5.api
```

### Method 3: Development mode with auto-reload

```bash
uvicorn pdmt5.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Verify API is running

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "mt5_connected": true,
  "mt5_version": "5.0.4321",
  "api_version": "1.0.0"
}
```

## API Documentation

Once the API is running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication

All API endpoints (except `/health` and `/docs`) require authentication via API key.

### Using API Key Header

```bash
curl -H "X-API-Key: your-secret-api-key-here" \
     http://localhost:8000/api/v1/symbols
```

## Basic Usage Examples

### Health Check

```bash
# No authentication required
curl http://localhost:8000/api/v1/health
```

Response:

```json
{
  "status": "healthy",
  "mt5_connected": true,
  "mt5_version": "5.0.4321",
  "api_version": "1.0.0"
}
```

### Get MT5 Version

```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/version
```

### List All Symbols

```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/symbols
```

### Filter Symbols by Group

```bash
# Get all USD pairs
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/symbols?group=*USD*"

# Get all Forex symbols
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/symbols?group=Forex*"
```

### Get Symbol Information

```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/symbols/EURUSD
```

Response:

```json
{
  "data": {
    "name": "EURUSD",
    "bid": 1.0856,
    "ask": 1.0857,
    "spread": 10,
    "digits": 5,
    "point": 0.00001,
    "trade_mode": 4,
    ...
  },
  "count": 1,
  "format": "json"
}
```

### Get Latest Tick

```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/symbols/EURUSD/tick
```

### Get Historical Rates (Candles)

```bash
# Get 100 H1 candles from a specific date
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/rates/from?symbol=EURUSD&timeframe=60&date_from=2024-01-01T00:00:00Z&count=100"
```

Response:

```json
{
  "data": [
    {
      "time": "2024-01-01T00:00:00",
      "open": 1.1045,
      "high": 1.1052,
      "low": 1.1042,
      "close": 1.1048,
      "tick_volume": 1523,
      "spread": 10,
      "real_volume": 0
    },
    ...
  ],
  "count": 100,
  "format": "json"
}
```

### Get Rates by Date Range

```bash
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/rates/range?symbol=EURUSD&timeframe=60&date_from=2024-01-01T00:00:00Z&date_to=2024-01-02T00:00:00Z"
```

### Get Tick Data

```bash
# Get last 1000 ticks
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/ticks/from?symbol=EURUSD&date_from=2024-01-01T00:00:00Z&count=1000&flags=6"
```

Flags:

- `2` = COPY_TICKS_INFO (only price changes)
- `4` = COPY_TICKS_TRADE (only trades)
- `6` = COPY_TICKS_ALL (all ticks, default)

### Get Account Information

```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/account
```

Response:

```json
{
  "data": {
    "login": 12345678,
    "balance": 10000.00,
    "equity": 10050.25,
    "profit": 50.25,
    "margin": 100.00,
    "margin_free": 9950.25,
    "margin_level": 10050.25,
    ...
  },
  "count": 1,
  "format": "json"
}
```

### Get Open Positions

```bash
# Get all positions
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/positions

# Filter by symbol
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/positions?symbol=EURUSD"
```

### Get Pending Orders

```bash
curl -H "X-API-Key: YOUR_KEY" \
     http://localhost:8000/api/v1/orders
```

### Get Historical Orders

```bash
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/history/orders?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z"
```

### Get Historical Deals

```bash
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/history/deals?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z&symbol=EURUSD"
```

## Format Selection

### JSON Format (default)

```bash
# Using Accept header
curl -H "X-API-Key: YOUR_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/symbols

# Using query parameter
curl -H "X-API-Key: YOUR_KEY" \
     "http://localhost:8000/api/v1/symbols?format=json"
```

### Parquet Format

```bash
# Using Accept header (recommended)
curl -H "X-API-Key: YOUR_KEY" \
     -H "Accept: application/parquet" \
     -o symbols.parquet \
     http://localhost:8000/api/v1/symbols

# Using query parameter
curl -H "X-API-Key: YOUR_KEY" \
     -o rates.parquet \
     "http://localhost:8000/api/v1/rates/from?symbol=EURUSD&timeframe=60&date_from=2024-01-01T00:00:00Z&count=1000&format=parquet"
```

### Reading Parquet files

```python
import pandas as pd

# Read the downloaded Parquet file
df = pd.read_parquet('symbols.parquet')
print(df.head())
```

### When to use Parquet

- **Use Parquet for**: Large datasets (>1000 records), data analysis, archival storage
- **Use JSON for**: Small queries, web frontends, debugging, human readability

Typical size reduction with Parquet: 50-80% compared to JSON

## Python Client Example

```python
import httpx
import pandas as pd
from datetime import datetime, timezone

class MT5Client:
    """Python client for MT5 REST API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.Client(
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

    def get_symbols(self, group: str | None = None) -> pd.DataFrame:
        """Get available symbols."""
        params = {"group": group} if group else {}
        response = self.client.get(f"{self.base_url}/api/v1/symbols", params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data["data"])

    def get_rates(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime,
        count: int
    ) -> pd.DataFrame:
        """Get historical rates."""
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "date_from": date_from.isoformat(),
            "count": count
        }
        response = self.client.get(f"{self.base_url}/api/v1/rates/from", params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["data"])
        df['time'] = pd.to_datetime(df['time'])
        return df

    def get_account(self) -> dict:
        """Get account information."""
        response = self.client.get(f"{self.base_url}/api/v1/account")
        response.raise_for_status()
        return response.json()["data"]

# Usage
client = MT5Client("http://localhost:8000", "YOUR_API_KEY")

# Get symbols
symbols = client.get_symbols(group="*USD*")
print(symbols)

# Get EURUSD H1 data
rates = client.get_rates(
    symbol="EURUSD",
    timeframe=60,
    date_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
    count=100
)
print(rates)

# Get account info
account = client.get_account()
print(f"Balance: {account['balance']}, Equity: {account['equity']}")
```

## Error Handling

The API returns standard HTTP status codes and RFC 7807 Problem Details format for errors.

### Common Status Codes

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Symbol not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: MT5 terminal not connected

### Error Response Format

```json
{
  "type": "/errors/mt5-disconnected",
  "title": "MT5 Terminal Not Connected",
  "status": 503,
  "detail": "MetaTrader5 terminal is not running or not logged in. Please start MT5 and login.",
  "instance": "/api/v1/symbols/EURUSD"
}
```

### Python Error Handling

```python
try:
    response = client.get(f"{base_url}/api/v1/symbols/INVALID")
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    error = e.response.json()
    print(f"Error {error['status']}: {error['title']}")
    print(f"Detail: {error['detail']}")
```

## Testing

### Run Test Suite

```bash
# Run all tests
uv run pytest tests/test_api/ -v

# Run specific test file
uv run pytest tests/test_api/test_health.py -v

# Run with coverage
uv run pytest tests/test_api/ --cov=pdmt5.api --cov-report=html
```

### Manual Testing with httpie

```bash
# Install httpie
pip install httpie

# Make requests with httpie (cleaner syntax)
http GET localhost:8000/api/v1/health

http GET localhost:8000/api/v1/symbols \
    X-API-Key:YOUR_KEY \
    group=="*USD*"

http GET localhost:8000/api/v1/symbols/EURUSD \
    X-API-Key:YOUR_KEY \
    Accept:application/json
```

## Troubleshooting

### API won't start

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**: Install API extras: `pip install pdmt5[api]`

**Problem**: `Address already in use`
**Solution**: Change port: `uvicorn pdmt5.api.main:app --port 8001`

### MT5 Connection Issues

**Problem**: `"mt5_connected": false` in health check
**Solution**:

1. Ensure MT5 terminal is running
2. Login to MT5 with valid credentials
3. Check MT5_LOGIN, MT5_PASSWORD, MT5_SERVER in .env
4. Verify MT5 terminal allows automated trading (Tools > Options > Expert Advisors)

**Problem**: `503 Service Unavailable` on all endpoints
**Solution**: MT5 terminal disconnected. Restart MT5 and login.

### Authentication Issues

**Problem**: `401 Unauthorized`
**Solution**:

- Check API key is correct in request header
- Verify X-API-Key header name (case-sensitive)
- Ensure API_KEY environment variable is set

### Performance Issues

**Problem**: Slow responses for large datasets
**Solution**:

- Use Parquet format for datasets >1000 records
- Reduce count parameter in requests
- Consider pagination for very large queries

**Problem**: Timeout errors
**Solution**:

- Increase client timeout (default 30s)
- Request smaller date ranges
- Check MT5 terminal is responsive

## Production Deployment

### Windows Service

```powershell
# Install NSSM (Non-Sucking Service Manager)
choco install nssm

# Create Windows service
nssm install MT5-API "C:\Python311\Scripts\uvicorn.exe" "pdmt5.api.main:app --host 0.0.0.0 --port 8000"

# Set working directory
nssm set MT5-API AppDirectory "C:\path\to\pdmt5"

# Set environment variables
nssm set MT5-API AppEnvironmentExtra API_KEY=your-key-here

# Start service
nssm start MT5-API
```

### HTTPS with Self-Signed Certificate

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with HTTPS
uvicorn pdmt5.api.main:app \
    --host 0.0.0.0 \
    --port 8443 \
    --ssl-keyfile=key.pem \
    --ssl-certfile=cert.pem
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 443 ssl;
    server_name mt5api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring

```bash
# Health check endpoint for monitoring
curl -f http://localhost:8000/api/v1/health || exit 1

# Add to cron for periodic checks
*/5 * * * * curl -f http://localhost:8000/api/v1/health || systemctl restart mt5-api
```

## Next Steps

- Review [data-model.md](./data-model.md) for detailed API models
- Check [contracts/openapi.yaml](./contracts/openapi.yaml) for full API specification
- Read [plan.md](./plan.md) for implementation details
- Explore Swagger UI at http://localhost:8000/docs for interactive testing

## Support

- GitHub Issues: https://github.com/dceoy/pdmt5/issues
- Documentation: https://github.com/dceoy/pdmt5
