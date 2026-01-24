# pdmt5 API Documentation

Pandas-based data handler for MetaTrader 5 trading platform.

## Overview

pdmt5 is a Python library that provides a pandas-based interface for handling MetaTrader 5 trading data. It simplifies data manipulation and analysis tasks for financial trading applications.

## Features

- **MetaTrader 5 Integration**: Direct connection to MetaTrader 5 platform (Windows only)
- **Pandas-based**: Leverages pandas for efficient data manipulation
- **Type Safety**: Built with pydantic for robust data validation
- **Financial Focus**: Designed specifically for trading and financial data analysis

## Installation

```bash
pip install pdmt5
```

### Quick Start

```python
from pdmt5 import Mt5Client, Mt5Config, Mt5DataClient, Mt5TradingClient
import MetaTrader5 as mt5
from datetime import datetime

# Configure connection
config = Mt5Config(
    login=12345678,
    password="your_password",
    server="YourBroker-Server",
    timeout=60000,
    portable=False
)

# Low-level API access with context manager
with Mt5Client() as client:
    client.initialize()
    client.login(config.login, config.password, config.server)
    account = client.account_info()
    rates = client.copy_rates_from("EURUSD", mt5.TIMEFRAME_H1, datetime.now(), 100)

# Pandas-friendly interface with automatic initialization
with Mt5DataClient(config=config) as client:
    # Get symbol information as DataFrame
    symbols_df = client.get_symbols_as_df()
    # Get OHLCV data as DataFrame
    rates_df = client.copy_rates_from_as_df(
        "EURUSD", mt5.TIMEFRAME_H1, datetime.now(), 100
    )
    # Get account info as DataFrame
    account_df = client.get_account_info_as_df()

# Trading operations with dry run support
with Mt5TradingClient(config=config, dry_run=True) as client:
    # Check open positions as DataFrame
    positions_df = client.get_positions_as_df()
    # Close positions for specific symbol (dry run)
    results = client.close_open_positions("EURUSD")
```

## Requirements

- Python 3.11+
- Windows OS (MetaTrader 5 requirement)
- MetaTrader 5 platform

## API Reference

Browse the API documentation to learn about available modules and functions:

- [Mt5Client](api/mt5.md) - Base client for low-level MT5 API access with context manager support
- [Mt5DataClient & Mt5Config](api/dataframe.md) - Pandas-friendly data client with DataFrame conversions
- [Mt5TradingClient](api/trading.md) - Advanced trading operations with position management
- [Utility Functions](api/utils.md) - Helper decorators and functions for data processing

## Development

This project follows strict code quality standards:

- Type hints required (strict mode)
- Comprehensive linting with Ruff
- Test coverage tracking
- Google-style docstrings

## License

MIT License - see [LICENSE](https://github.com/dceoy/pdmt5/blob/main/LICENSE) file for details.
