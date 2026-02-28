---
name: mt5-symbols
description: List available trading symbols, get detailed symbol information, or fetch the latest tick for a symbol from the MT5 API. Use when the user wants to browse symbols, look up symbol details, or check current prices.
allowed-tools: Bash
---

# MT5 Symbols

Query symbol-related endpoints on the mt5api.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
All endpoints require the `X-API-Key` header. Set `MT5_API_KEY` in the environment.

## Endpoints

### List Symbols

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/api/v1/symbols" | python -m json.tool
```

Optional query parameters:

| Parameter | Type   | Description                                   |
|-----------|--------|-----------------------------------------------|
| group     | string | Symbol group filter (e.g., `*USD*`, `Forex*`) |

Example with filter:

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/api/v1/symbols?group=*USD*" | python -m json.tool
```

### Get Symbol Info

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/api/v1/symbols/EURUSD" | python -m json.tool
```

Path parameters:

| Parameter | Type   | Description                   |
|-----------|--------|-------------------------------|
| symbol    | string | Symbol name (e.g., `EURUSD`)  |

### Get Latest Tick

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/api/v1/symbols/EURUSD/tick" | python -m json.tool
```

Path parameters:

| Parameter | Type   | Description  |
|-----------|--------|--------------|
| symbol    | string | Symbol name  |

## Procedure

1. Identify which symbol operation the user needs (list, info, or tick).
2. Substitute the correct symbol name and optional filters into the URL.
3. Run the `curl` command and parse the JSON response.
4. Summarize the results, highlighting key fields such as bid/ask prices, spread, symbol properties, or available symbols.
