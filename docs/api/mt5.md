# Mt5Client

::: pdmt5.mt5

## Overview

The Mt5Client module provides the base client class for connecting to MetaTrader 5 and performing core operations. This is the foundation class that handles the low-level MT5 API interactions and provides basic error handling and connection management.

## Classes

### Mt5Client

::: pdmt5.mt5.Mt5Client
options:
show_bases: false

Base client class for MetaTrader 5 operations with connection management and error handling.

### Mt5RuntimeError

::: pdmt5.mt5.Mt5RuntimeError
options:
show_bases: false

Custom runtime exception for MetaTrader 5 specific errors.

## Usage Examples

### Basic Connection

```python
import MetaTrader5 as mt5
from pdmt5.mt5 import Mt5Client

# Create client
client = Mt5Client(mt5=mt5)

# Use as context manager
with client:
    # Initialize connection
    success = client.initialize()
    if success:
        print("Connected to MetaTrader 5")

        # Get version info
        version = client.version()
        print(f"MT5 Version: {version}")

        # Get account info
        account = client.account_info()
        print(f"Account: {account}")
```

### Connection with Login

```python
with client:
    # Initialize with path
    client.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")

    # Login to specific account
    success = client.login(
        login=12345,
        password="your_password",
        server="broker_server"
    )

    if success:
        print("Logged in successfully")
```

### Symbol Operations

```python
with client:
    client.initialize()

    # Get total number of symbols
    total = client.symbols_total()
    print(f"Total symbols: {total}")

    # Get all symbols
    symbols = client.symbols_get()
    print(f"First 5 symbols: {symbols[:5]}")

    # Get symbols by group
    forex_symbols = client.symbols_get(group="*USD*")

    # Get specific symbol info
    symbol_info = client.symbol_info("EURUSD")
    print(f"EURUSD info: {symbol_info}")

    # Get current tick
    tick = client.symbol_info_tick("EURUSD")
    print(f"Current EURUSD tick: {tick}")
```

### Market Data Retrieval

```python
from datetime import datetime
import MetaTrader5 as mt5

with client:
    client.initialize()

    # Get OHLCV rates from specific date
    rates = client.copy_rates_from(
        symbol="EURUSD",
        timeframe=mt5.TIMEFRAME_H1,
        date_from=datetime(2024, 1, 1),
        count=100
    )

    # Get rates within date range
    rates_range = client.copy_rates_range(
        symbol="EURUSD",
        timeframe=mt5.TIMEFRAME_D1,
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 31)
    )

    # Get tick data
    ticks = client.copy_ticks_from(
        symbol="EURUSD",
        date_from=datetime(2024, 1, 1),
        count=1000,
        flags=mt5.COPY_TICKS_ALL
    )
```

### Trading Operations

```python
with client:
    client.initialize()
    client.login(12345, "password", "server")

    # Get current positions
    positions = client.positions_get()
    print(f"Open positions: {len(positions) if positions else 0}")

    # Get current orders
    orders = client.orders_get()
    print(f"Pending orders: {len(orders) if orders else 0}")

    # Calculate margin requirement
    margin = client.order_calc_margin(
        action=mt5.ORDER_TYPE_BUY,
        symbol="EURUSD",
        volume=1.0,
        price=1.1000
    )
    print(f"Required margin: {margin}")

    # Calculate profit
    profit = client.order_calc_profit(
        action=mt5.ORDER_TYPE_BUY,
        symbol="EURUSD",
        volume=1.0,
        price_open=1.1000,
        price_close=1.1050
    )
    print(f"Calculated profit: {profit}")
```

### Historical Data

```python
from datetime import datetime

with client:
    client.initialize()

    # Get historical orders
    history_orders = client.history_orders_get(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 31)
    )

    # Get historical deals
    history_deals = client.history_deals_get(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 31)
    )

    # Get specific order by ticket
    order = client.history_orders_get(ticket=123456)
```

### Market Book Operations

```python
with client:
    client.initialize()

    # Subscribe to market depth
    success = client.market_book_add("EURUSD")
    if success:
        print("Subscribed to EURUSD market depth")

        # Get market book
        book = client.market_book_get("EURUSD")
        print(f"Market book: {book}")

        # Unsubscribe
        client.market_book_release("EURUSD")
```

## Connection Management

The Mt5Client supports both explicit and context manager usage:

```python
# Explicit initialization
client = Mt5Client(mt5=mt5)
client.initialize()
try:
    # Your trading operations
    account = client.account_info()
finally:
    client.shutdown()

# Context manager (recommended)
with Mt5Client(mt5=mt5) as client:
    client.initialize()
    # Your trading operations
    account = client.account_info()
```

## Error Handling

All methods include proper error handling and raise `Mt5RuntimeError` with detailed information when operations fail:

```python
from pdmt5.mt5 import Mt5RuntimeError

try:
    with client:
        client.initialize()
        rates = client.copy_rates_from("INVALID", mt5.TIMEFRAME_H1, datetime.now(), 100)
except Mt5RuntimeError as e:
    print(f"MetaTrader 5 error: {e}")
```

## Logging

The client includes comprehensive logging for all operations:

```python
import logging

# Enable debug logging to see all MT5 operations
logging.basicConfig(level=logging.DEBUG)

with client:
    client.initialize()  # Will log initialization details
    account = client.account_info()  # Will log account retrieval
```

## Method Categories

### Connection Management

- `initialize()` - Initialize MT5 connection
- `login()` - Login to trading account
- `shutdown()` - Close connection
- `version()` - Get MT5 version
- `last_error()` - Get last error details

### Account & Terminal

- `account_info()` - Get account information
- `terminal_info()` - Get terminal status and settings

### Symbol Management

- `symbols_total()` - Get total number of symbols
- `symbols_get()` - Get symbol list
- `symbol_info()` - Get symbol information
- `symbol_info_tick()` - Get current tick
- `symbol_select()` - Add/remove symbol from Market Watch

### Market Data

- `copy_rates_from()` - Get OHLCV rates from date
- `copy_rates_from_pos()` - Get OHLCV rates from position
- `copy_rates_range()` - Get OHLCV rates in date range
- `copy_ticks_from()` - Get ticks from date
- `copy_ticks_range()` - Get ticks in date range

### Market Book

- `market_book_add()` - Subscribe to market depth
- `market_book_release()` - Unsubscribe from market depth
- `market_book_get()` - Get market book data

### Trading

- `orders_total()` - Get number of pending orders
- `orders_get()` - Get pending orders
- `positions_total()` - Get number of open positions
- `positions_get()` - Get open positions
- `order_calc_margin()` - Calculate required margin
- `order_calc_profit()` - Calculate profit
- `order_check()` - Validate order request
- `order_send()` - Send trading order

### History

- `history_orders_total()` - Get historical orders count
- `history_orders_get()` - Get historical orders
- `history_deals_total()` - Get historical deals count
- `history_deals_get()` - Get historical deals

## Best Practices

1. **Always use context manager** for automatic connection management
2. **Handle errors gracefully** with try-except blocks
3. **Initialize before operations** - call `initialize()` after creating the client
4. **Use logging** to debug connection and operation issues
5. **Check return values** - many methods return None on failure
6. **Use appropriate timeframes** and date ranges for data requests
7. **Subscribe/unsubscribe** to market book properly to avoid resource leaks
