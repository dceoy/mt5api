---
name: mt5api
description: >-
  Query the MT5 API for account info, terminal status, health checks, last
  error, symbol data, market data (OHLCV rates, ticks, market depth), open
  positions, pending orders, trade history, record counts, margin/profit
  calculations, order checks, live order submission, and reconnecting the MT5
  terminal with new credentials. Use when the user wants to interact with any mt5api endpoint.
allowed-tools: Bash
---

# MT5 API

Query all mt5api endpoints: health, version, last error, account, terminal,
symbols, market data, positions, orders, trade history, record totals,
margin/profit calculations, order checks, live order submission (opt-in), and
market-depth subscriptions.

## Configuration

The API base URL defaults to `http://localhost:8000`. Set `MT5API_URL` to
override. When the server mounts routes under `MT5API_ROUTER_PREFIX`, include
that prefix in `MT5API_URL` (e.g., `http://localhost:8000/mt5`). When the server
is configured with `MT5API_SECRET_KEY`, send the same value in the `X-API-Key`
header. When server-side auth is disabled, omit the header instead of sending
an empty `X-API-Key`.

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
  subscriptions before logging in. Confirm the target `login`/`server` with the
  user before sending it. The password must not appear in any reply or log
  because it grants access to a trading account; the response only confirms
  `login`, `server`, `timeout`, and `connected`.
- State-changing calls are `POST` endpoints: `/connection/login`,
  `/symbols/{symbol}/select`, `/market-book/{symbol}/subscribe|unsubscribe`, and
  `/order/send`. Everything else is read-only (`/order/check` only validates a
  request and never places an order).
- `/order/send` submits a live order on the connected account and is disabled
  unless the server sets `MT5API_ENABLE_ORDER_SEND=true` and
  `MT5API_SECRET_KEY`; otherwise it returns `403`. Use it only when the user
  explicitly asks to place an order, and confirm the full request first.
- Historical queries need either `(date_from AND date_to)` or
  `(ticket OR position)`.
- If `/health` reports `unhealthy`, the MT5 terminal may not be running or
  reachable.

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
| api_version   | string  | API version                    |

### MT5 Version

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/version" | python -m json.tool
```

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------- | ------------------------ |
| format    | string | no       | Response format override |

### Last MT5 Error

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/last-error" | python -m json.tool
```

Useful for diagnosing a failed call or an `unhealthy` terminal.

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

### Count Symbols

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/symbols/total" | python -m json.tool
```

Returns `{"total": N}`.

### Select Symbol in MarketWatch

State-changing. Adds a symbol to the MarketWatch window or removes it.

```bash
curl -s -X POST "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/symbols/EURUSD/select?enable=true" | python -m json.tool
```

| Parameter | Type | Required | Default | Description                            |
| --------- | ---- | -------- | ------- | -------------------------------------- |
| enable    | bool | no       | `true`  | `true` to show, `false` to hide symbol |

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

### Subscribe / Unsubscribe Market Depth (experimental)

State-changing. Subscribe before reading `/market-book/{symbol}` when DOM data
is needed, and unsubscribe when done.

```bash
curl -s -X POST "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/market-book/EURUSD/subscribe" | python -m json.tool
curl -s -X POST "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/market-book/EURUSD/unsubscribe" | python -m json.tool
```

Active subscriptions are capped by the server; exceeding the cap returns `429`
with a problem-details body. Unsubscribe from another symbol and retry.

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

### Record Totals

Return `{"total": N}` without transferring the records.

```bash
curl -s "${AUTH_HEADER[@]}" "${MT5API_URL}/positions/total" | python -m json.tool
curl -s "${AUTH_HEADER[@]}" "${MT5API_URL}/orders/total" | python -m json.tool
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/history/orders/total?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
  | python -m json.tool
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/history/deals/total?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z" \
  | python -m json.tool
```

The history totals take `date_from` and `date_to` (ISO 8601).

---

## Calculations & Order Checks

### Margin and Profit

```bash
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/calc/margin?action=ORDER_TYPE_BUY&symbol=EURUSD&volume=0.1&price=1.085" \
  | python -m json.tool
curl -s "${AUTH_HEADER[@]}" \
  "${MT5API_URL}/calc/profit?action=ORDER_TYPE_BUY&symbol=EURUSD&volume=0.1&price_open=1.085&price_close=1.09" \
  | python -m json.tool
```

| Parameter   | Type    | Required | Endpoint | Description                                                         |
| ----------- | ------- | -------- | -------- | ------------------------------------------------------------------- |
| action      | str/int | yes      | both     | MT5 order type: `ORDER_TYPE_BUY`, alias `BUY`, or the integer value |
| symbol      | string  | yes      | both     | Symbol name                                                         |
| volume      | float   | yes      | both     | Trade volume in lots (`> 0`)                                        |
| price       | float   | yes      | margin   | Open price (`> 0`)                                                  |
| price_open  | float   | yes      | profit   | Open price (`> 0`)                                                  |
| price_close | float   | yes      | profit   | Close price (`> 0`)                                                 |

Returns `{"margin": ...}` or `{"profit": ...}` in the account currency.

### Check Order

Validates a trade request without placing an order. The body is
`{"request": {...}}`; required fields depend on the MT5 `action`:

| `action` | Operation | Required trade fields                                                               |
| -------- | --------- | ----------------------------------------------------------------------------------- |
| `1`      | DEAL      | `symbol`, `volume`, `type`                                                          |
| `5`      | PENDING   | `symbol`, `volume`, `type`, `price`                                                 |
| `6`      | SLTP      | `position` or `symbol`, plus `sl` and `tp`                                          |
| `7`      | MODIFY    | `order`, `price`, `sl`, `tp`, `type_time`; also `expiration` for `type_time` 2 or 3 |
| `8`      | REMOVE    | `order`                                                                             |
| `10`     | CLOSE_BY  | `position`, `position_by`                                                           |

Other supported fields include `stoplimit`, `deviation`, `magic`, `comment`,
`type_filling`, `type_time`, and `expiration`. `price` is optional for
DEAL (market execution). Unknown fields are rejected. `/order/send` uses the
same trade-request schema; see `/openapi.json` for full field definitions.

```bash
curl -s -X POST "${AUTH_HEADER[@]}" \
  -H 'Content-Type: application/json' \
  -d '{"request": {"action": 1, "symbol": "EURUSD", "volume": 0.1, "type": "ORDER_TYPE_BUY", "price": 1.085}}' \
  "${MT5API_URL}/order/check" | python -m json.tool
```

### Send Order (live trading, opt-in)

Submits a real order through MT5 `order_send`. Run it only after the user has
confirmed the exact request, `expected_login`, and `expected_server`, because it
can open or close positions with real money. Authentication must be enabled
(`AUTH_HEADER` set); an invalid key returns `401`.

```bash
curl -s -X POST "${AUTH_HEADER[@]}" \
  -H 'Content-Type: application/json' \
  -d '{"request": {"action": 1, "symbol": "EURUSD", "volume": 0.1, "type": "ORDER_TYPE_BUY", "price": 1.085}, "expected_login": 12345678, "expected_server": "Broker-Demo"}' \
  "${MT5API_URL}/order/send" | python -m json.tool
```

| Field           | Type   | Required | Description                                          |
| --------------- | ------ | -------- | ---------------------------------------------------- |
| request         | object | yes      | MT5 trade request (same shape as `/order/check`)     |
| expected_login  | int    | yes      | Account the order is intended for (`> 0`)            |
| expected_server | string | no       | Trade server the order is intended for (exact match) |

The server returns `409` and sends nothing when the connected account differs
from `expected_login` (or `expected_server`). It does not call `order_check` or
retry. HTTP `200` does not mean the order filled: always read the returned MT5
`retcode` and report it.

Do not automatically retry after a timeout, disconnection, cancellation, or
unparseable response: MT5 may have accepted the order even if no result was
received. First reconcile the outcome against `/positions`, `/orders`, and
`/history/deals` or `/history/orders`. If execution remains uncertain, stop
and obtain explicit user confirmation before considering another submission.

---

## Procedure

1. Pick the endpoint(s) that answer the request, and collect any missing
   required parameters (symbol, timeframe, dates, count, filters).
2. Choose JSON or Parquet output. Build `AUTH_HEADER` only when
   `MT5API_SECRET_KEY` is set, then run the `curl` command(s).
3. Summarize the parsed JSON, or note that Parquet data was returned. Quote
   MT5 error text from `503` responses and suggest `/last-error` for more
   detail.
4. Before any state-changing `POST` (see Operational Notes), confirm the
   target with the user.
