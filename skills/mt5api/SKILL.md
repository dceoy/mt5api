---
name: mt5api
description: >-
  Query the MT5 API for account info, terminal status, health checks, symbol
  data, market data (OHLCV rates, ticks, market depth), open positions, pending
  orders, and trade history. Use when the user wants to interact with any mt5api
  endpoint.
allowed-tools: Bash
---

# MT5 API

Query all mt5api endpoints: health, version, account, terminal, symbols, market
data, positions, orders, and trade history.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to
override. When the server is configured with `MT5_API_KEY`, send the same value
in the `X-API-Key` header. If server-side auth is disabled, the header is
optional.

## Response Formats

All endpoints (except `/health`) return JSON by default. Request Parquet with
`format=parquet` or `Accept: application/parquet`.

---

## Health & Version

### Health Check (public, no auth required)

```bash
curl -s "${MT5_API_URL:-http://localhost:8000}/health" | python -m json.tool
```

Returns:

| Field         | Type    | Description                    |
| ------------- | ------- | ------------------------------ |
| status        | string  | `healthy` or `unhealthy`       |
| mt5_connected | bool    | MT5 terminal connection status |
| mt5_version   | string? | MT5 terminal version string    |
| api_version   | string  | API version (e.g., `1.0.0`)   |

### MT5 Version

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/version" | python -m json.tool
```

---

## Account & Terminal

### Account Info

Get current trading account details (balance, equity, margin, leverage, etc.).

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/account" | python -m json.tool
```

Key fields: `login`, `balance`, `equity`, `margin`, `margin_free`,
`margin_level`, `leverage`, `currency`, `server`, `name`.

### Terminal Info

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/terminal" | python -m json.tool
```

---

## Symbols

### List Symbols

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols" | python -m json.tool
```

| Parameter | Type   | Required | Description                                   |
| --------- | ------ | -------- | --------------------------------------------- |
| group     | string | no       | Symbol group filter (e.g., `*USD*`, `Forex*`) |
| format    | string | no       | Response format override                      |

### Get Symbol Info

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols/EURUSD" | python -m json.tool
```

### Get Latest Tick

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/symbols/EURUSD/tick" | python -m json.tool
```

---

## Market Data

`timeframe` and `flags` accept either the official MetaTrader 5 constant name
(e.g., `TIMEFRAME_H1`, `COPY_TICKS_ALL`) or the equivalent integer value.

### Rates from Date

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/rates/from?symbol=EURUSD&timeframe=TIMEFRAME_H1&date_from=2024-01-01T00:00:00Z&count=100" \
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
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/rates/from-pos?symbol=EURUSD&timeframe=TIMEFRAME_H1&start_pos=0&count=100" \
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
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/rates/range?symbol=EURUSD&timeframe=TIMEFRAME_H1&date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
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
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/ticks/from?symbol=EURUSD&date_from=2024-01-02T10:00:00Z&count=500" \
  | python -m json.tool
```

| Parameter | Type     | Required | Default | Description                       |
| --------- | -------- | -------- | ------- | --------------------------------- |
| symbol    | string   | yes      |         | Symbol name                       |
| date_from | datetime | yes      |         | Start date (ISO 8601)             |
| count     | int      | yes      |         | Number of ticks (1–100000)        |
| flags     | int/str  | no       | 6       | MT5 tick flag constant or integer |
| format    | string   | no       |         | Response format override          |

### Ticks in Range

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/ticks/range?symbol=EURUSD&date_from=2024-01-02T10:00:00Z&date_to=2024-01-02T11:00:00Z" \
  | python -m json.tool
```

| Parameter | Type     | Required | Default | Description                       |
| --------- | -------- | -------- | ------- | --------------------------------- |
| symbol    | string   | yes      |         | Symbol name                       |
| date_from | datetime | yes      |         | Start date (ISO 8601)             |
| date_to   | datetime | yes      |         | End date (ISO 8601)               |
| flags     | int/str  | no       | 6       | MT5 tick flag constant or integer |
| format    | string   | no       |         | Response format override          |

### Market Book (DOM)

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/market-book/EURUSD" | python -m json.tool
```

---

## Positions, Orders & History

### Open Positions

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/positions" | python -m json.tool
```

| Parameter | Type   | Required | Description               |
| --------- | ------ | -------- | ------------------------- |
| symbol    | string | no       | Filter by symbol          |
| group     | string | no       | Filter by group pattern   |
| ticket    | int    | no       | Filter by position ticket |
| format    | string | no       | Response format override  |

### Pending Orders

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/orders" | python -m json.tool
```

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| symbol    | string | no       | Filter by symbol         |
| group     | string | no       | Filter by group pattern  |
| ticket    | int    | no       | Filter by order ticket   |
| format    | string | no       | Response format override |

### Historical Orders

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/history/orders?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
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
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/history/deals?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
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
4. Construct and run the appropriate `curl` command(s).
5. Parse the JSON response and summarize the results, or note when the API
   returned Parquet data.
6. If the health status is `unhealthy`, note that the MT5 terminal may not be
   running or reachable.
7. For historical queries, remind the user that either a date range or a
   ticket/position filter is required.
