# pdmt5

Pandas-based data handler for MetaTrader 5

[![CI/CD](https://github.com/dceoy/pdmt5/actions/workflows/ci.yml/badge.svg)](https://github.com/dceoy/pdmt5/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)](https://www.microsoft.com/windows)

## Overview

**pdmt5** is a Python package that provides a pandas-based interface for MetaTrader 5 (MT5), making it easier to work with financial market data in Python. It automatically converts MT5's native data structures into pandas DataFrames, enabling seamless integration with data science workflows.

### Key Features

- 📊 **Pandas Integration**: All data returned as pandas DataFrames for easy analysis
- 🔧 **Type Safety**: Full type hints with strict pyright checking and pydantic validation
- 🏦 **Comprehensive MT5 Coverage**: Account info, market data, tick data, orders, positions, and more
- 🚀 **Context Manager Support**: Clean initialization and cleanup with `with` statements
- 📈 **Time Series Ready**: OHLCV data with proper datetime indexing
- 🛡️ **Robust Error Handling**: Custom exceptions with detailed MT5 error information
- 💰 **Advanced Trading Operations**: Position management, margin calculations, and risk analysis tools
- 🧪 **Dry Run Mode**: Test trading strategies without executing real trades

## Requirements

- **Operating System**: Windows (required by MetaTrader5 API)
- **Python**: 3.11 or higher
- **MetaTrader 5**: Terminal must be installed

## Installation

### Using pip

```bash
pip install -U pdmt5 MetaTrader5
```

### Using uv

```bash
git clone https://github.com/dceoy/pdmt5.git
cd pdmt5
uv sync
```

## Quick Start

```python
import MetaTrader5 as mt5
from datetime import datetime
from pdmt5 import Mt5DataClient, Mt5Config

# Configure connection
config = Mt5Config(
    login=12345678,
    password="your_password",
    server="YourBroker-Server",
    timeout=60000
)

# Use as context manager
with Mt5DataClient(config=config) as client:
    # Get account information as DataFrame
    account_info = client.account_info_as_df()
    print(account_info)

    # Get OHLCV data as DataFrame
    rates = client.copy_rates_from_as_df(
        symbol="EURUSD",
        timeframe=mt5.TIMEFRAME_H1,
        date_from=datetime(2024, 1, 1),
        count=100
    )
    print(rates.head())

    # Get current positions as DataFrame
    positions = client.positions_get_as_df()
    print(positions)
```

## Core Components

### Mt5Client

The base client wrapper for all MetaTrader5 operations with context manager support:

- **Connection Management**:
  - `initialize()` - Establish connection with MT5 terminal (with optional path, login, password, server, timeout)
  - `login()` - Connect to trading account with credentials
  - `shutdown()` - Close MT5 terminal connection
  - Context manager support (`with` statement) for automatic initialization/cleanup
- **Terminal Information**:
  - `version()` - Get MT5 terminal version, build, and release date
  - `last_error()` - Get last error code and description
  - `account_info()` - Get current trading account information
  - `terminal_info()` - Get terminal status and settings
- **Symbol Operations**:
  - `symbols_total()` - Get total number of financial instruments
  - `symbols_get()` - Get all symbols or filter by group
  - `symbol_info()` - Get detailed data on specific symbol
  - `symbol_info_tick()` - Get last tick for symbol
  - `symbol_select()` - Show/hide symbol in MarketWatch
- **Market Depth**:
  - `market_book_add()` - Subscribe to Market Depth events
  - `market_book_get()` - Get current Market Depth data
  - `market_book_release()` - Unsubscribe from Market Depth
- **Market Data**:
  - `copy_rates_from()` - Get bars from specified date
  - `copy_rates_from_pos()` - Get bars from specified position
  - `copy_rates_range()` - Get bars for date range
  - `copy_ticks_from()` - Get ticks from specified date
  - `copy_ticks_range()` - Get ticks for date range
- **Order Operations**:
  - `orders_total()` - Get number of active orders
  - `orders_get()` - Get active orders with optional filters
  - `order_calc_margin()` - Calculate required margin
  - `order_calc_profit()` - Calculate potential profit
  - `order_check()` - Check if order can be placed
  - `order_send()` - Send order to trade server
- **Position Operations**:
  - `positions_total()` - Get number of open positions
  - `positions_get()` - Get open positions with optional filters
- **Trading History**:
  - `history_orders_total()` - Get number of historical orders
  - `history_orders_get()` - Get historical orders with filters
  - `history_deals_total()` - Get number of historical deals
  - `history_deals_get()` - Get historical deals with filters

### Mt5DataClient

Extends Mt5Client with pandas DataFrame and dictionary conversions:

- **Enhanced Connection**:
  - `initialize_and_login_mt5()` - Combined initialization and login with retry logic
  - Configurable retry attempts via `retry_count` parameter
- **DataFrame/Dictionary Conversions**: All methods have both `_as_df` and `_as_dict` variants:
  - `version_as_dict/df()` - MT5 version information
  - `last_error_as_dict/df()` - Last error details
  - `account_info_as_dict/df()` - Account information
  - `terminal_info_as_dict/df()` - Terminal information
  - `symbols_get_as_dicts/df()` - Symbol list with optional group filter
  - `symbol_info_as_dict/df()` - Single symbol information
  - `symbol_info_tick_as_dict/df()` - Last tick data
  - `market_book_get_as_dicts/df()` - Market depth data
- **OHLCV Data Methods**:
  - `copy_rates_from_as_dicts/df()` - Historical bars from date
  - `copy_rates_from_pos_as_dicts/df()` - Historical bars from position
  - `copy_rates_range_as_dicts/df()` - Historical bars for date range
- **Tick Data Methods**:
  - `copy_ticks_from_as_dicts/df()` - Historical ticks from date
  - `copy_ticks_range_as_dicts/df()` - Historical ticks for date range
- **Trading Data Methods**:
  - `orders_get_as_dicts/df()` - Active orders with filters
  - `order_check_as_dict/df()` - Order validation results
  - `order_send_as_dict/df()` - Order execution results
  - `positions_get_as_dicts/df()` - Open positions with filters
  - `history_orders_get_as_dicts/df()` - Historical orders with date/ticket/position filters
  - `history_deals_get_as_dicts/df()` - Historical deals with date/ticket/position filters
- **Features**:
  - Automatic time conversion to datetime objects
  - Optional DataFrame indexing with `index_keys` parameter
  - Input validation for dates, counts, and positions
  - Pydantic-based configuration via `Mt5Config`

### Mt5TradingClient

Advanced trading operations client that extends Mt5DataClient:

- **Position Management**:
  - `close_open_positions()` - Close all positions for specified symbol(s)
  - `place_market_order()` - Place market orders with configurable side, volume, and execution modes
  - `update_sltp_for_open_positions()` - Modify stop loss and take profit levels for open positions
- **Margin Calculations**:
  - `calculate_minimum_order_margin()` - Calculate minimum required margin for a specific order side
  - `calculate_volume_by_margin()` - Calculate maximum volume for given margin amount
  - `calculate_spread_ratio()` - Calculate normalized bid-ask spread ratio
  - `calculate_new_position_margin_ratio()` - Calculate margin ratio for potential new positions
- **Simplified Data Access**:
  - `fetch_latest_rates_as_df()` - Get recent OHLC data with timeframe strings (e.g., "M1", "H1", "D1")
  - `fetch_latest_ticks_as_df()` - Get tick data for specified seconds around last tick
  - `collect_entry_deals_as_df()` - Filter and collect entry deals (BUY/SELL) from history
  - `fetch_positions_with_metrics_as_df()` - Get open positions with calculated metrics (elapsed time, margin, profit ratios)
- **Features**:
  - Smart order routing with configurable filling modes
  - Comprehensive error handling with `Mt5TradingError`
  - Support for batch operations on multiple symbols
  - Automatic position closing with proper order type reversal

### Configuration

```python
from pdmt5 import Mt5Config

config = Mt5Config(
    login=12345678,          # MT5 account number
    password="password",     # MT5 password
    server="Broker-Server",  # MT5 server name
    timeout=60000           # Connection timeout in ms
)
```

## Examples

### Getting Historical Data

```python
import MetaTrader5 as mt5
from datetime import datetime

with Mt5DataClient(config=config) as client:
    # Get last 1000 H1 bars for EURUSD as DataFrame
    df = client.copy_rates_from_as_df(
        symbol="EURUSD",
        timeframe=mt5.TIMEFRAME_H1,
        date_from=datetime.now(),
        count=1000
    )

    # Data includes: time, open, high, low, close, tick_volume, spread, real_volume
    print(df.columns)
    print(df.describe())
```

### Working with Tick Data

```python
from datetime import datetime, timedelta

with Mt5DataClient(config=config) as client:
    # Get ticks for the last hour as DataFrame
    ticks = client.copy_ticks_from_as_df(
        symbol="EURUSD",
        date_from=datetime.now() - timedelta(hours=1),
        count=10000,
        flags=mt5.COPY_TICKS_ALL
    )

    # Tick data includes: time, bid, ask, last, volume, flags
    print(ticks.head())
```

### Analyzing Positions

```python
with Mt5DataClient(config=config) as client:
    # Get all open positions as DataFrame
    positions = client.positions_get_as_df()

    if not positions.empty:
        # Calculate summary statistics
        summary = positions.groupby('symbol').agg({
            'volume': 'sum',
            'profit': 'sum',
            'price_open': 'mean'
        })
        print(summary)
```

### Trading Operations

```python
from pdmt5 import Mt5TradingClient

# Create trading client
with Mt5TradingClient(config=config) as trader:
    # Place a market buy order
    order_result = trader.place_market_order(
        symbol="EURUSD",
        volume=0.1,
        order_side="BUY",
        order_filling_mode="IOC",  # Immediate or Cancel
        order_time_mode="GTC"      # Good Till Cancelled
    )
    print(f"Order placed: {order_result['retcode']}")

    # Update stop loss and take profit for open positions
    update_results = trader.update_sltp_for_open_positions(
        symbol="EURUSD",
        stop_loss=1.0950,   # New stop loss
        take_profit=1.1050  # New take profit
    )
    for result in update_results:
        print(f"Position updated: {result['retcode']}")

    # Calculate margin ratio for a new position
    margin_ratio = trader.calculate_new_position_margin_ratio(
        symbol="EURUSD",
        new_position_side="SELL",
        new_position_volume=0.2
    )
    print(f"New position margin ratio: {margin_ratio:.2%}")

    # Close all EURUSD positions with specific order filling mode
    results = trader.close_open_positions(
        symbols="EURUSD",
        order_filling_mode="FOK"  # Fill or Kill
    )

    if results:
        for symbol, close_results in results.items():
            for result in close_results:
                print(f"Closed position {result.get('position')} with result: {result['retcode']}")
```

### Market Analysis with Mt5TradingClient

```python
with Mt5TradingClient(config=config) as trader:
    # Calculate spread ratio for EURUSD
    spread_ratio = trader.calculate_spread_ratio("EURUSD")
    print(f"EURUSD spread ratio: {spread_ratio:.5f}")

    # Get minimum order margin for BUY and SELL
    buy_margin = trader.calculate_minimum_order_margin("EURUSD", "BUY")
    sell_margin = trader.calculate_minimum_order_margin("EURUSD", "SELL")
    print(f"Minimum BUY margin: {buy_margin['margin']} (volume: {buy_margin['volume']})")
    print(f"Minimum SELL margin: {sell_margin['margin']} (volume: {sell_margin['volume']})")

    # Calculate volume by margin
    available_margin = 1000.0
    max_buy_volume = trader.calculate_volume_by_margin("EURUSD", available_margin, "BUY")
    max_sell_volume = trader.calculate_volume_by_margin("EURUSD", available_margin, "SELL")
    print(f"Max BUY volume for ${available_margin}: {max_buy_volume}")
    print(f"Max SELL volume for ${available_margin}: {max_sell_volume}")

    # Get recent OHLC data with custom timeframe
    rates_df = trader.fetch_latest_rates_as_df(
        symbol="EURUSD",
        granularity="M15",  # 15-minute bars
        count=100
    )
    print(rates_df.tail())

    # Get tick data for the last 60 seconds
    ticks_df = trader.fetch_latest_ticks_as_df(
        symbol="EURUSD",
        seconds=60
    )
    print(f"Received {len(ticks_df)} ticks")

    # Collect entry deals for the last hour
    deals_df = trader.collect_entry_deals_as_df(
        symbol="EURUSD",
        history_seconds=3600
    )
    if not deals_df.empty:
        print(f"Found {len(deals_df)} entry deals")
        print(deals_df[['time', 'type', 'volume', 'price']].head())

    # Get positions with calculated metrics
    positions_df = trader.fetch_positions_with_metrics_as_df("EURUSD")
    if not positions_df.empty:
        print(f"Open positions with metrics:")
        print(positions_df[['ticket', 'volume', 'profit', 'elapsed_seconds', 'underlier_profit_ratio']].head())
```

## REST API (Under Development)

**pdmt5** has a planned FastAPI-based REST API for MT5 data access. The
implementation is not available yet, so the API is not runnable and the public
HTTP surface is subject to change.

For the current specification and design work, see:

- [docs/api/rest-api.md](docs/api/rest-api.md)
- [specs/041-mt5-rest-api/quickstart.md](specs/041-mt5-rest-api/quickstart.md)

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/dceoy/pdmt5.git
cd pdmt5

# Install with uv
uv sync

# Run tests
uv run pytest tests/ -v

# Run type checking
uv run pyright .

# Run linting
uv run ruff check --fix .
uv run ruff format .
```

### Code Quality

This project maintains high code quality standards:

- **Type Checking**: Strict mode with pyright
- **Linting**: Comprehensive ruff configuration with 40+ rule categories
- **Testing**: pytest with coverage tracking (minimum 90%)
- **Documentation**: Google-style docstrings

## Error Handling

The package provides detailed error information:

```python
from pdmt5 import Mt5RuntimeError

try:
    with Mt5DataClient(config=config) as client:
        data = client.copy_rates_from("INVALID", mt5.TIMEFRAME_H1, datetime.now(), 100)
except Mt5RuntimeError as e:
    print(f"MT5 Error: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Description: {e.description}")
```

## Limitations

- **Windows Only**: Due to MetaTrader5 API requirements
- **MT5 Terminal Required**: The MetaTrader 5 terminal must be installed
- **Single Thread**: MT5 API is not thread-safe

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Ensure tests pass and coverage is maintained
4. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Daichi Narushima, Ph.D.

## Acknowledgments

- MetaTrader 5 for providing the Python API
- The pandas community for the excellent data manipulation tools
