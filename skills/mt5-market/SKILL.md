---
name: mt5-market
description: Fetch historical OHLCV rates, tick data, or market depth (DOM) from the MT5 API. Use when the user needs candlestick data, price history, tick-level data, or order book depth for a trading symbol.
allowed-tools: Bash
---

# MT5 Market Data

Query market data endpoints on the mt5api for historical rates, ticks, and market depth.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
When the server is configured with `MT5_API_KEY`, send the same value in the
`X-API-Key` header. If server-side auth is disabled, the header is optional.
`timeframe` and `flags` accept either the official MetaTrader 5 constant name
(for example `TIMEFRAME_H1`, `COPY_TICKS_ALL`) or the equivalent integer value.

## Response Formats

All market-data endpoints return JSON by default. Request Parquet with
`format=parquet` or `Accept: application/parquet`.

## Endpoints

### Rates from Date

Get historical OHLCV candles starting from a specific date.

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

Get historical OHLCV candles starting from a bar index.

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

Get historical OHLCV candles for a date range.

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

Get tick-level data starting from a date.

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

Get tick-level data for a date range.

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

Get market depth (order book) for a symbol.

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/market-book/EURUSD" | python -m json.tool
```

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| symbol    | string | yes      | Symbol name              |
| format    | string | no       | Response format override |

## Procedure

1. Identify which market data endpoint the user needs.
2. Gather the required parameters (symbol, timeframe, dates, count).
3. Decide whether the caller needs JSON or Parquet output.
4. Construct and run the appropriate `curl` command.
5. Parse the JSON response and summarize the data (number of records, date
   range covered, OHLCV summary, etc.), or note when the API returned Parquet
   data.
6. If the user requests Parquet format, add `format=parquet` or set
   `Accept: application/parquet`.
