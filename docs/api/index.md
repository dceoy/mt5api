# API Reference

This section contains the complete API documentation for pdmt5.

## Modules

The pdmt5 package consists of the following modules:

### [Mt5Client](mt5.md)

Base client class for MetaTrader 5 operations with connection management, low-level API access, and error handling (`Mt5RuntimeError`).

### [Mt5DataClient & Mt5Config](dataframe.md)

Core data client functionality and configuration, providing pandas-friendly interface to MetaTrader 5.

### [Mt5TradingClient](trading.md)

Advanced trading operations including position management, order analysis, and trading performance metrics with dry run support.

### [REST API](rest-api.md)

FastAPI-based REST API that exposes read-only MT5 data over HTTP with JSON and Parquet support.

### [Deployment](deployment.md)

Windows service deployment guide for hosting the REST API alongside MetaTrader 5.

## Architecture Overview

The package follows a layered architecture:

1. **Base Layer** (`mt5.py`): Provides the base `Mt5Client` class with low-level MT5 API access and `Mt5RuntimeError` exception
2. **Data Layer** (`dataframe.py`): Extends `Mt5Client` with configuration (`Mt5Config`) and pandas-friendly `Mt5DataClient` class
3. **Trading Layer** (`trading.py`): Extends `Mt5DataClient` with advanced trading operations and `Mt5TradingError` exception
4. **Utilities** (`utils.py`): Helper functions for time conversion and DataFrame manipulation

## Usage Guidelines

All modules follow these conventions:

- **Type Safety**: All functions include comprehensive type hints
- **Error Handling**: Centralized through `Mt5RuntimeError` with meaningful error messages
- **Documentation**: Google-style docstrings with examples
- **Validation**: Pydantic models for data validation and configuration
- **pandas Integration**: All data returns as DataFrames with proper datetime indexing

## Quick Start

```python
from pdmt5 import Mt5Client, Mt5Config, Mt5DataClient, Mt5TradingClient
import MetaTrader5 as mt5
from datetime import datetime

# Low-level API access with Mt5Client
with Mt5Client(mt5=mt5) as client:
    client.initialize()
    account = client.account_info()
    rates = client.copy_rates_from("EURUSD", mt5.TIMEFRAME_H1, datetime.now(), 100)

# Pandas-friendly interface with Mt5DataClient and configuration
config = Mt5Config(login=12345, password="pass", server="MetaQuotes-Demo")
with Mt5DataClient(mt5=mt5, config=config) as client:
    symbols_df = client.symbols_get_as_df()
    rates_df = client.copy_rates_from_as_df("EURUSD", mt5.TIMEFRAME_H1, datetime.now(), 100)

# Advanced trading operations with Mt5TradingClient
with Mt5TradingClient(mt5=mt5, config=config, dry_run=True) as client:
    # Close all positions for a symbol
    results = client.close_open_positions("EURUSD")
```

## Examples

See individual module pages for detailed usage examples and code samples.
