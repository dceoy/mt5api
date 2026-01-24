# Trading

::: pdmt5.trading

## Overview

The trading module extends Mt5DataClient with advanced trading operations including position management, order execution, and dry run support for testing trading strategies without actual execution.

## Classes

### Mt5TradingClient

::: pdmt5.trading.Mt5TradingClient
options:
show_bases: false

Advanced trading client class that inherits from `Mt5DataClient` and provides specialized trading functionality.

### Mt5TradingError

::: pdmt5.trading.Mt5TradingError
options:
show_bases: false

Custom runtime exception for trading-specific errors.

## Usage Examples

### Basic Trading Operations

```python
import MetaTrader5 as mt5
from pdmt5 import Mt5TradingClient, Mt5Config

# Create configuration
config = Mt5Config(
    login=123456,
    password="your_password",
    server="broker_server",
    timeout=60000,
    portable=False
)

# Create client with dry run mode for testing
client = Mt5TradingClient(config=config, dry_run=True)

# Use as context manager
with client:
    # Get current positions as DataFrame
    positions_df = client.get_positions_as_df()
    print(f"Open positions: {len(positions_df)}")

    # Close positions for specific symbol
    results = client.close_open_positions("EURUSD")
    print(f"Closed positions: {results}")
```

### Production Trading

```python
# Create client for live trading (dry_run=False)
client = Mt5TradingClient(config=config, dry_run=False)

with client:
    # Close all positions for multiple symbols
    results = client.close_open_positions(["EURUSD", "GBPUSD", "USDJPY"])

    # Close all positions (all symbols)
    all_results = client.close_open_positions()
```

### Order Filling Modes

```python
with Mt5TradingClient(config=config) as client:
    # Use IOC (Immediate or Cancel) - default
    results_ioc = client.close_open_positions(
        symbols="EURUSD",
        order_filling_mode="IOC"
    )

    # Use FOK (Fill or Kill)
    results_fok = client.close_open_positions(
        symbols="GBPUSD",
        order_filling_mode="FOK"
    )

    # Use RETURN (Return if not filled)
    results_return = client.close_open_positions(
        symbols="USDJPY",
        order_filling_mode="RETURN"
    )
```

### Custom Order Parameters

```python
with client:
    # Close positions with custom parameters and order filling mode
    results = client.close_open_positions(
        "EURUSD",
        order_filling_mode="IOC",  # Specify per method call
        comment="Closing all EURUSD positions",
        deviation=10  # Maximum price deviation
    )
```

### Error Handling

```python
from pdmt5.trading import Mt5TradingError

try:
    with client:
        results = client.close_open_positions("EURUSD")
except Mt5TradingError as e:
    print(f"Trading error: {e}")
    # Handle specific trading errors
```

### Checking Order Status

```python
with client:
    # Check order (note: send_or_check_order is an internal method)
    # For trading operations, use the provided methods like close_open_positions

    # Example: Check if we can close a position
    positions = client.get_positions_as_df()
    if not positions.empty:
        # Close specific position
        results = client.close_open_positions("EURUSD")
```

## Position Management Features

The Mt5TradingClient provides intelligent position management:

- **Automatic Position Reversal**: Automatically determines the correct order type to close positions
- **Batch Operations**: Close multiple positions for one or more symbols
- **Dry Run Support**: Test trading logic without executing real trades
- **Flexible Filtering**: Close positions by symbol, group, or all positions
- **Custom Parameters**: Support for additional order parameters like comment, deviation, etc.

## Dry Run Mode

Dry run mode is essential for testing trading strategies:

```python
# Test mode - validates orders without execution
test_client = Mt5TradingClient(config=config, dry_run=True)

# Production mode - executes real orders
prod_client = Mt5TradingClient(config=config, dry_run=False)
```

In dry run mode:

- Orders are validated using `order_check()` instead of `order_send()`
- No actual trades are executed
- Full validation of margin requirements and order parameters
- Same return structure as live trading for easy testing

## Return Values

The `close_open_positions()` method returns a dictionary with symbols as keys:

```python
{
    "EURUSD": [
        {
            "retcode": 10009,  # Trade done
            "deal": 123456,
            "order": 789012,
            "volume": 1.0,
            "price": 1.1000,
            "comment": "Request executed",
            ...
        }
    ],
    "GBPUSD": [...]
}
```

## Best Practices

1. **Always use dry run mode first** to test your trading logic
2. **Handle Mt5TradingError exceptions** for proper error management
3. **Check return codes** to verify successful execution
4. **Use context managers** for automatic connection handling
5. **Log trading operations** for audit trails
6. **Validate positions exist** before attempting to close them
7. **Consider market hours** and trading session times

## Common Return Codes

- `TRADE_RETCODE_DONE` (10009): Trade operation completed successfully
- `TRADE_RETCODE_TRADE_DISABLED`: Trading disabled for the account
- `TRADE_RETCODE_MARKET_CLOSED`: Market is closed
- `TRADE_RETCODE_NO_MONEY`: Insufficient funds
- `TRADE_RETCODE_INVALID_VOLUME`: Invalid trade volume

## Margin Calculation Methods

The trading client provides advanced margin calculation capabilities:

### Calculate Minimum Order Margin

```python
with client:
    # Calculate minimum margin required for BUY order
    min_margin_buy = client.calculate_minimum_order_margin("EURUSD", "BUY")
    print(f"Minimum volume: {min_margin_buy['volume']}")
    print(f"Minimum margin: {min_margin_buy['margin']}")

    # Calculate minimum margin required for SELL order
    min_margin_sell = client.calculate_minimum_order_margin("EURUSD", "SELL")
```

### Calculate Volume by Margin

```python
with client:
    # Calculate maximum volume for given margin amount
    available_margin = 1000.0  # USD
    max_volume_buy = client.calculate_volume_by_margin("EURUSD", available_margin, "BUY")
    max_volume_sell = client.calculate_volume_by_margin("EURUSD", available_margin, "SELL")

    print(f"Max BUY volume for ${available_margin}: {max_volume_buy}")
    print(f"Max SELL volume for ${available_margin}: {max_volume_sell}")
```

### Calculate New Position Margin Ratio

```python
with client:
    # Calculate margin ratio for potential new position
    margin_ratio = client.calculate_new_position_margin_ratio(
        symbol="EURUSD",
        new_position_side="BUY",
        new_position_volume=1.0
    )
    print(f"New position would use {margin_ratio:.2%} of account equity")

    # Check if adding position would exceed risk limits
    if margin_ratio > 0.1:  # 10% risk limit
        print("Position size too large for risk management")
```

## Market Order Placement

Place market orders with flexible configuration:

```python
with client:
    # Place a BUY market order
    result = client.place_market_order(
        symbol="EURUSD",
        volume=1.0,
        order_side="BUY",
        order_filling_mode="IOC",  # Immediate or Cancel
        order_time_mode="GTC",     # Good Till Cancelled
        dry_run=False,             # Set to True for testing
        comment="My buy order"
    )

    # Place a SELL market order with FOK filling
    result = client.place_market_order(
        symbol="EURUSD",
        volume=0.5,
        order_side="SELL",
        order_filling_mode="FOK",  # Fill or Kill
        dry_run=True  # Test mode
    )

    print(f"Order result: {result}")
```

## Stop Loss and Take Profit Management

Update SL/TP for existing positions:

```python
with client:
    # Update SL/TP for all EURUSD positions
    results = client.update_sltp_for_open_positions(
        symbol="EURUSD",
        stop_loss=1.0950,
        take_profit=1.1100,
        dry_run=False
    )

    # Update only specific positions by ticket
    results = client.update_sltp_for_open_positions(
        symbol="EURUSD",
        stop_loss=1.0950,
        tickets=[123456, 789012],  # Specific position tickets
        dry_run=True
    )
```

## Market Data and Analysis Methods

### Spread Analysis

```python
with client:
    # Calculate spread ratio for symbol
    spread_ratio = client.calculate_spread_ratio("EURUSD")
    print(f"EURUSD spread ratio: {spread_ratio:.6f}")
```

### OHLC Data Retrieval

```python
with client:
    # Fetch latest rate data as DataFrame
    rates_df = client.fetch_latest_rates_as_df(
        symbol="EURUSD",
        granularity="M1",  # 1-minute bars
        count=1440,        # Last 24 hours
        index_keys="time"
    )
    print(f"Latest rates: {rates_df.tail()}")
```

### Tick Data Analysis

```python
with client:
    # Fetch recent tick data
    ticks_df = client.fetch_latest_ticks_as_df(
        symbol="EURUSD",
        seconds=300,           # Last 5 minutes
        index_keys="time_msc"
    )
    print(f"Tick count: {len(ticks_df)}")
```

### Position Analytics with Enhanced Metrics

```python
with client:
    # Get positions with additional calculated metrics
    positions_df = client.fetch_positions_with_metrics_as_df("EURUSD")

    if not positions_df.empty:
        print("Position metrics:")
        print(f"Total signed volume: {positions_df['signed_volume'].sum()}")
        print(f"Total signed margin: {positions_df['signed_margin'].sum()}")
        print(f"Average profit ratio: {positions_df['underlier_profit_ratio'].mean():.4f}")
```

### Deal History Analysis

```python
with client:
    # Collect entry deals for analysis
    deals_df = client.collect_entry_deals_as_df(
        symbol="EURUSD",
        history_seconds=3600,  # Last hour
        index_keys="ticket"
    )

    if not deals_df.empty:
        print(f"Entry deals found: {len(deals_df)}")
        print(f"Deal types: {deals_df['type'].value_counts()}")
```

## Integration with Mt5DataClient

Since Mt5TradingClient inherits from Mt5DataClient, all data retrieval methods are available:

```python
with Mt5TradingClient(config=config) as client:
    # Get current positions as DataFrame
    positions_df = client.get_positions_as_df()

    # Analyze positions
    if not positions_df.empty:
        # Calculate total exposure
        total_volume = positions_df['volume'].sum()

        # Close losing positions
        losing_positions = positions_df[positions_df['profit'] < 0]
        for symbol in losing_positions['symbol'].unique():
            client.close_open_positions(symbol)

    # Risk management with margin calculations
    for symbol in ["EURUSD", "GBPUSD", "USDJPY"]:
        # Calculate current margin usage
        current_ratio = client.calculate_new_position_margin_ratio(symbol)
        print(f"{symbol} current margin ratio: {current_ratio:.2%}")

        # Calculate maximum safe position size
        safe_margin = 500.0  # USD
        max_safe_volume = client.calculate_volume_by_margin(symbol, safe_margin, "BUY")
        print(f"{symbol} max safe volume: {max_safe_volume}")
```
