---
name: mt5-symbols
description: List available trading symbols, get detailed symbol information, or fetch the latest tick for a symbol from the MT5 API. Use when the user wants to browse symbols, look up symbol details, or check current prices.
allowed-tools: Bash
---

# MT5 Symbols

Query symbol-related endpoints on the mt5api.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
When the server is configured with `MT5_API_KEY`, send the same value in the
`X-API-Key` header. If server-side auth is disabled, the header is optional.

## Response Formats

All symbol endpoints return JSON by default. Request Parquet with
`format=parquet` or `Accept: application/parquet`.

## Endpoints

### List Symbols

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols" | python -m json.tool
```

Optional query parameters:

| Parameter | Type   | Description                                   |
| --------- | ------ | --------------------------------------------- |
| group     | string | Symbol group filter (e.g., `*USD*`, `Forex*`) |
| format    | string | Optional response format: `json` or `parquet` |

Example with filter:

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols?group=*USD*" | python -m json.tool
```

### Get Symbol Info

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols/EURUSD" | python -m json.tool
```

Path parameters:

| Parameter | Type   | Description                  |
| --------- | ------ | ---------------------------- |
| symbol    | string | Symbol name (e.g., `EURUSD`) |

Optional query parameters:

| Parameter | Type   | Description                       |
| --------- | ------ | --------------------------------- |
| format    | string | Optional response format override |

### Get Latest Tick

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols/EURUSD/tick" | python -m json.tool
```

Path parameters:

| Parameter | Type   | Description |
| --------- | ------ | ----------- |
| symbol    | string | Symbol name |

Optional query parameters:

| Parameter | Type   | Description                       |
| --------- | ------ | --------------------------------- |
| format    | string | Optional response format override |

## Procedure

1. Identify which symbol operation the user needs (list, info, or tick).
2. Substitute the correct symbol name and optional filters into the URL.
3. Decide whether the caller needs JSON or Parquet output.
4. Run the `curl` command and parse the JSON response, or note when the API
   returned Parquet data.
5. Summarize the results, highlighting key fields such as bid/ask prices,
   spread, symbol properties, or available symbols.
