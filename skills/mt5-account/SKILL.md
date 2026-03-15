---
name: mt5-account
description: Retrieve MT5 trading account information or terminal details from the MT5 API. Use when the user wants to check account balance, equity, margin, leverage, or terminal status.
allowed-tools: Bash
---

# MT5 Account & Terminal

Query account and terminal information endpoints on the mt5api.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
When the server is configured with `MT5_API_KEY`, send the same value in the
`X-API-Key` header. If server-side auth is disabled, the header is optional.

## Response Formats

Both endpoints return JSON by default. Request Parquet with `format=parquet`
or `Accept: application/parquet`.

## Endpoints

### Account Info

Get current trading account details (balance, equity, margin, leverage, etc.).

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/account" | python -m json.tool
```

Returns a `DataResponse` containing account fields such as:

- `login` - Account number
- `balance` - Account balance
- `equity` - Account equity
- `margin` - Used margin
- `margin_free` - Free margin
- `margin_level` - Margin level percentage
- `leverage` - Account leverage
- `currency` - Account currency
- `server` - Trade server name
- `name` - Account holder name

Example requesting Parquet:

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/account?format=parquet" \
  > account.parquet
```

### Terminal Info

Get MetaTrader 5 terminal information.

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/terminal" | python -m json.tool
```

Returns a `DataResponse` with terminal details such as build number, platform, data path, and connection status.

## Procedure

1. Determine whether the user needs account info or terminal info.
2. Decide whether the caller needs JSON or Parquet output.
3. Run the appropriate `curl` command.
4. Parse and summarize the JSON response, highlighting key financial metrics
   (balance, equity, margin) for account queries or connection status for
   terminal queries, or note when the API returned Parquet data.
