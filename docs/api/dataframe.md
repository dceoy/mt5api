# DataFrame

::: pdmt5.dataframe

## Overview

The dataframe module extends the base Mt5Client with pandas-friendly functionality for connecting to MetaTrader 5 and retrieving trading data as pandas DataFrames. It includes configuration management, automatic data conversion, and comprehensive validation utilities.

## Classes

### Mt5Config

::: pdmt5.dataframe.Mt5Config
options:
show_bases: false

Configuration class for MetaTrader 5 connection parameters using pydantic for validation.

### Mt5DataClient

::: pdmt5.dataframe.Mt5DataClient
options:
show_bases: false

Extended client class that inherits from `Mt5Client` and provides a pandas-friendly interface to MetaTrader 5 functions with automatic DataFrame conversion.

## Usage Examples

### Basic Connection

```python
import MetaTrader5 as mt5
from pdmt5.dataframe import Mt5DataClient, Mt5Config

# Create configuration
config = Mt5Config(
    login=123456,
    password="your_password",
    server="broker_server"
)

# Create client
client = Mt5DataClient(mt5=mt5, config=config)

# Use as context manager
with client:
    # Get account information
    account_df = client.account_info()
    print(account_df)
```

### Retrieving Market Data

```python
from datetime import datetime
import MetaTrader5 as mt5

with client:
    # Get OHLCV data
    rates_df = client.copy_rates_from(
        symbol="EURUSD",
        timeframe=mt5.TIMEFRAME_H1,
        date_from=datetime(2024, 1, 1),
        count=1000
    )

    # Get tick data
    ticks_df = client.copy_ticks_from(
        symbol="EURUSD",
        date_from=datetime(2024, 1, 1),
        count=1000,
        flags=mt5.COPY_TICKS_ALL
    )
```

### Symbol Information

```python
with client:
    # Get all symbols
    symbols_df = client.symbols_get()

    # Get specific symbol info
    symbol_info_df = client.symbol_info("EURUSD")

    # Get current tick
    tick_df = client.symbol_info_tick("EURUSD")
```

### Trading History

```python
from datetime import datetime

with client:
    # Get historical orders
    orders_df = client.history_orders_get(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 31),
        symbol="EURUSD"
    )

    # Get historical deals
    deals_df = client.history_deals_get(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 31)
    )
```

### Current Positions and Orders

```python
with client:
    # Get current positions
    positions_df = client.positions_get()

    # Get current orders
    orders_df = client.orders_get(symbol="EURUSD")
```

## Data Conversion Features

The Mt5DataClient automatically handles:

- **Time Conversion**: Converts Unix timestamps to pandas datetime objects
- **Index Setting**: Sets appropriate datetime indexes for time-series data
- **DataFrame Creation**: Converts MetaTrader 5 named tuples to pandas DataFrames
- **Error Handling**: Provides meaningful error messages for failed operations
- **Empty Data**: Returns empty DataFrames when no data is available

## Error Handling

All methods raise `Mt5RuntimeError` exceptions with detailed error information when operations fail:

```python
from pdmt5.mt5 import Mt5RuntimeError

try:
    rates_df = client.copy_rates_from("INVALID", mt5.TIMEFRAME_H1, datetime.now(), 100)
except Mt5RuntimeError as e:
    print(f"MetaTrader 5 error: {e}")
```

## Connection Management

The client supports both explicit and context manager usage:

```python
# Explicit initialization
client.initialize()
try:
    # Your trading operations
    pass
finally:
    client.shutdown()

# Context manager (recommended)
with client:
    # Your trading operations
    pass
```

## Type Safety

All methods include comprehensive type hints and use pydantic for configuration validation, ensuring type safety throughout the codebase.
