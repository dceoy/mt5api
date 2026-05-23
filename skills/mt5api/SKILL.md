---
name: mt5api
description: >-
  Query the MT5 API for account info, terminal status, health checks, symbol
  data, market data (OHLCV rates, ticks, market depth), open positions, pending
  orders, trade history, and reconnecting the MT5 terminal with new
  credentials. Use when the user wants to interact with any mt5api endpoint.
allowed-tools: Bash
---

# MT5 API

Query all mt5api endpoints: health, version, account, terminal, symbols, market
data, positions, orders, and trade history.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5API_URL` to
override. When the server is configured with `MT5API_SECRET_KEY`, send the same value
in the `X-API-Key` header. When server-side auth is disabled, omit the header
instead of sending an empty `X-API-Key`.

Use these shell helpers in examples:

```bash
MT5API_URL="${MT5API_URL:-http://localhost:8000}"
AUTH_HEADER=()
if [ -n "${MT5API_SECRET_KEY:-}" ]; then
  AUTH_HEADER=(-H "X-API-Key: ${MT5API_SECRET_KEY}")
fi
```

Login credentials for `/connection/login` are read from the environment so
the password is never hard-coded in a command:

| Variable          | Description                                | Required for login |
| ----------------- | ------------------------------------------ | ------------------ |
| `MT5API_LOGIN`    | Trading account login (integer)            | yes                |
| `MT5API_PASSWORD` | Trading account password                   | yes                |
| `MT5API_SERVER`   | Trading server name (e.g., `Broker-Demo`)  | yes                |
| `MT5API_TIMEOUT`  | Connection timeout in milliseconds (`> 0`) | no                 |

## Response Formats

All endpoints (except `/health`) return JSON by default. Request Parquet with
`format=parquet` or `Accept: application/parquet`.

## Operational Notes

- Start `ticks/range` with a narrow window. Large ranges can be slow; use
  `ticks/from` when the user only needs the latest `N` ticks.
- `/market-book/{symbol}` may return `503` when MT5 depth-of-market data is not
  available for the symbol. Report the exact MT5 error and suggest another
  symbol or skipping DOM data.
- Empty arrays from `/positions`, `/orders`, `/history/orders`, or
  `/history/deals` are valid results.
- `/connection/login` reconnects the shared MT5 client to a different account.
  It shuts down the current connection and releases any active market-book
  subscriptions before logging in. Never echo the password back to the user
  and do not log it; the response only confirms `login`, `server`, `timeout`,
  and `connected`.

---

## Health & Version

### Health Check (public, no auth required)

```bash
curl -s "${MT5API_URL}/health" | python -m json.tool
```

Returns:

| Field         | Type    | Description                    |
| ------------- | ------- | ------------------------------ |
| status        | string  | `healthy` or `unhealthy`       |
| mt5_connected | bool    | MT5 terminal connection status |
| mt5_version   | string? | MT5 terminal version string    |
| api_version   | string  | API version (e.g., `1.0.0`)    |

### MT5 Version

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/version" | python -m json.tool
```

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| format    | string | no       | Response format override |

---

## Connection

### Reconnect to MT5

Shut down the current MT5 client and reconnect with new credentials. Active
market-book subscriptions are released first. The call is serialized so
concurrent reconnect attempts do not race. The password is sent only in the
request body and is never echoed in the response.

```bash
# Build JSON body from env vars; include timeout only when set
LOGIN_BODY=$(python3 -c "
import json, os, sys
body = {
    'login': int(os.environ['MT5API_LOGIN']),
    'password': os.environ['MT5API_PASSWORD'],
    'server': os.environ['MT5API_SERVER'],
}
t = os.environ.get('MT5API_TIMEOUT')
if t:
    body['timeout'] = int(t)
print(json.dumps(body))
")
curl -s -X POST "${AUTH_HEADER[@]}" \
  -H 'Content-Type: application/json' \
  -d "${LOGIN_BODY}" \
  "${MT5API_URL}/connection/login" | python -m json.tool
```

Request body:

| Field    | Type   | Required | Description                                |
| -------- | ------ | -------- | ------------------------------------------ |
| login    | int    | yes      | Trading account login (positive integer)   |
| password | string | yes      | Trading account password (never echoed)    |
| server   | string | yes      | Trading server name (e.g., `Broker-Demo`)  |
| timeout  | int    | no       | Connection timeout in milliseconds (`> 0`) |

Successful response (`200`):

| Field     | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| login     | int    | Login that was used to connect               |
| server    | string | Trading server that was connected to         |
| timeout   | int?   | Timeout in milliseconds if one was specified |
| connected | bool   | `true` when the new connection succeeded     |

On failure, MT5 errors surface as `503 Service Unavailable` with an RFC 7807
problem-details body. Never include the supplied password in any summary or
diagnostic you return to the user.

---

## Account & Terminal

### Account Info

Get current trading account details (balance, equity, margin, leverage, etc.).

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/account" | python -m json.tool
```

Key fields: `login`, `balance`, `equity`, `margin`, `margin_free`,
`margin_level`, `leverage`, `currency`, `server`, `name`.

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| format    | string | no       | Response format override |

### Terminal Info

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/terminal" | python -m json.tool
```

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| format    | string | no       | Response format override |

---

## Symbols

### List Symbols

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/symbols" | python -m json.tool
```

| Parameter | Type   | Required | Description                                   |
| --------- | ------ | -------- | --------------------------------------------- |
| group     | string | no       | Symbol group filter (e.g., `*USD*`, `Forex*`) |
| format    | string | no       | Response format override                      |

### Get Symbol Info

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/symbols/EURUSD" | python -m json.tool
```

### Get Latest Tick

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/symbols/EURUSD/tick" | python -m json.tool
```

---

## Market Data

`timeframe` and `flags` accept either the official MetaTrader 5 constant name
(e.g., `TIMEFRAME_H1`, `COPY_TICKS_ALL`) or the equivalent integer value.

### Rates from Date

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_H1&date_from=2024-01-01T00:00:00Z&count=100" \
  | python -m json.tool
```

| Parameter | Type     | Required | Description                                  |
| --------- | -------- | -------- | -------------------------------------------- |
| symbol    | string   | yes      | Symbol name                                  |
| timeframe | int/str  | yes      | MT5 timeframe constant or equivalent integer |
| date_from | datetime | yes      | Start date (ISO 8601)                        |
| count     | int      | yes      | Number of candles (1–100000)                 |
| format    | string   | no       | Response format override                     |

### Rates from Position

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/rates/from-pos?symbol=EURUSD&timeframe=TIMEFRAME_H1&start_pos=0&count=100" \
  | python -m json.tool
```

| Parameter | Type    | Required | Description                       |
| --------- | ------- | -------- | --------------------------------- |
| symbol    | str     | yes      | Symbol name                       |
| timeframe | str/int | yes      | MT5 timeframe constant or integer |
| start_pos | int     | yes      | Start position (0 = current bar)  |
| count     | int     | yes      | Number of candles (1–100000)      |
| format    | string  | no       | Response format override          |

### Rates in Range

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/rates/range?symbol=EURUSD&timeframe=TIMEFRAME_H1&date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
  | python -m json.tool
```

| Parameter | Type     | Required | Description                       |
| --------- | -------- | -------- | --------------------------------- |
| symbol    | string   | yes      | Symbol name                       |
| timeframe | int/str  | yes      | MT5 timeframe constant or integer |
| date_from | datetime | yes      | Start date (ISO 8601)             |
| date_to   | datetime | yes      | End date (ISO 8601)               |
| format    | string   | no       | Response format override          |

### Ticks from Date

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/ticks/from?symbol=EURUSD&date_from=2024-01-02T10:00:00Z&count=500" \
  | python -m json.tool
```

| Parameter | Type     | Required | Default        | Description                       |
| --------- | -------- | -------- | -------------- | --------------------------------- |
| symbol    | string   | yes      |                | Symbol name                       |
| date_from | datetime | yes      |                | Start date (ISO 8601)             |
| count     | int      | yes      |                | Number of ticks (1–100000)        |
| flags     | int/str  | no       | COPY_TICKS_ALL | MT5 tick flag constant or integer |
| format    | string   | no       |                | Response format override          |

### Ticks in Range

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/ticks/range?symbol=EURUSD&date_from=2024-01-02T10:00:00Z&date_to=2024-01-02T11:00:00Z" \
  | python -m json.tool
```

| Parameter | Type     | Required | Default        | Description                       |
| --------- | -------- | -------- | -------------- | --------------------------------- |
| symbol    | string   | yes      |                | Symbol name                       |
| date_from | datetime | yes      |                | Start date (ISO 8601)             |
| date_to   | datetime | yes      |                | End date (ISO 8601)               |
| flags     | int/str  | no       | COPY_TICKS_ALL | MT5 tick flag constant or integer |
| format    | string   | no       |                | Response format override          |

### Market Book (DOM)

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/market-book/EURUSD" | python -m json.tool
```

If this returns `503`, explain that MT5 did not provide DOM data for the
requested symbol and include the server's error text.

---

## Positions, Orders & History

### Open Positions

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/positions" | python -m json.tool
```

| Parameter | Type   | Required | Description               |
| --------- | ------ | -------- | ------------------------- |
| symbol    | string | no       | Filter by symbol          |
| group     | string | no       | Filter by group pattern   |
| ticket    | int    | no       | Filter by position ticket |
| format    | string | no       | Response format override  |

### Pending Orders

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/orders" | python -m json.tool
```

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| symbol    | string | no       | Filter by symbol         |
| group     | string | no       | Filter by group pattern  |
| ticket    | int    | no       | Filter by order ticket   |
| format    | string | no       | Response format override |

### Historical Orders

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/history/orders?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
  | python -m json.tool
```

| Parameter | Type     | Required | Description                                       |
| --------- | -------- | -------- | ------------------------------------------------- |
| date_from | datetime | cond.    | Start date (required if no ticket/position)       |
| date_to   | datetime | cond.    | End date (required if no ticket/position)         |
| ticket    | int      | cond.    | Filter by ticket (alternative to date range)      |
| position  | int      | cond.    | Filter by position ID (alternative to date range) |
| symbol    | string   | no       | Filter by symbol                                  |
| group     | string   | no       | Filter by group pattern                           |
| format    | string   | no       | Response format override                          |

Either `(date_from AND date_to)` or `(ticket OR position)` must be provided.

### Historical Deals

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/history/deals?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
  | python -m json.tool
```

| Parameter | Type     | Required | Description                                       |
| --------- | -------- | -------- | ------------------------------------------------- |
| date_from | datetime | cond.    | Start date (required if no ticket/position)       |
| date_to   | datetime | cond.    | End date (required if no ticket/position)         |
| ticket    | int      | cond.    | Filter by ticket (alternative to date range)      |
| position  | int      | cond.    | Filter by position ID (alternative to date range) |
| symbol    | string   | no       | Filter by symbol                                  |
| group     | string   | no       | Filter by group pattern                           |
| format    | string   | no       | Response format override                          |

Either `(date_from AND date_to)` or `(ticket OR position)` must be provided.

---

## Procedure

1. Identify which endpoint(s) the user needs from the sections above.
2. Gather required parameters (symbol, timeframe, dates, count, filters).
3. Decide whether the caller needs JSON or Parquet output.
4. Build `AUTH_HEADER` only when `MT5API_SECRET_KEY` is set, then construct and run
   the appropriate `curl` command(s).
5. For `ticks/range`, start with a narrow interval and widen only if needed.
6. Parse the JSON response and summarize the results, or note when the API
   returned Parquet data.
7. If `/market-book/{symbol}` returns `503`, explain that MT5 did not provide
   DOM data for that symbol and include the error text.
8. If the health status is `unhealthy`, note that the MT5 terminal may not be
   running or reachable.
9. For historical queries, remind the user that either a date range or a
   ticket/position filter is required.
10. For `/connection/login`, always send the password in the POST body and
    never repeat it in any reply or log message. If the user asks you to
    reconnect, confirm the target `login`/`server` before sending the request.
