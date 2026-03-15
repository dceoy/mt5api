---
name: mt5-history
description: Query open positions, pending orders, historical orders, and historical deals from the MT5 API. Use when the user wants to check current trades, pending orders, or trade history.
allowed-tools: Bash
---

# MT5 Positions, Orders & History

Query trading state and history endpoints on the mt5api.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5_API_URL` to override.
All endpoints require the `X-API-Key` header. Set `MT5_API_KEY` in the environment.

## Endpoints

### Open Positions

Get current open positions with optional filters.

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/positions" | python -m json.tool
```

| Parameter | Type   | Required | Description               |
| --------- | ------ | -------- | ------------------------- |
| symbol    | string | no       | Filter by symbol          |
| group     | string | no       | Filter by group pattern   |
| ticket    | int    | no       | Filter by position ticket |

Example with symbol filter:

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/positions?symbol=EURUSD" | python -m json.tool
```

### Pending Orders

Get current pending orders with optional filters.

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/orders" | python -m json.tool
```

| Parameter | Type   | Required | Description             |
| --------- | ------ | -------- | ----------------------- |
| symbol    | string | no       | Filter by symbol        |
| group     | string | no       | Filter by group pattern |
| ticket    | int    | no       | Filter by order ticket  |

### Historical Orders

Get historical orders filtered by date range or ticket/position.

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

Either `(date_from AND date_to)` or `(ticket OR position)` must be provided.

Example by ticket:

```bash
curl -s -H "X-API-Key: ${MT5_API_KEY}" \
  "${MT5_API_URL:-http://localhost:8000}/history/orders?ticket=123456" \
  | python -m json.tool
```

### Historical Deals

Get historical deals filtered by date range or ticket/position.

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

Either `(date_from AND date_to)` or `(ticket OR position)` must be provided.

## Procedure

1. Identify the user's query: open positions, pending orders, historical orders, or historical deals.
2. Gather required filters (dates, symbol, ticket, or position).
3. Construct and run the `curl` command with the appropriate query parameters.
4. Parse the JSON response and summarize the results (number of records, P/L for positions, order types, deal volumes, etc.).
5. For historical queries, remind the user that either a date range or a ticket/position filter is required.
