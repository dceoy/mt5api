# Utilities

::: pdmt5.utils

## Overview

The utils module provides internal utility functions and decorators used throughout the pdmt5 package for data transformation and DataFrame manipulation.

## Functions

### detect_and_convert_time_to_datetime

::: pdmt5.utils.detect_and_convert_time_to_datetime
options:
show_bases: false

Decorator that automatically converts time values to datetime objects based on the result type.

### set_index_if_possible

::: pdmt5.utils.set_index_if_possible
options:
show_bases: false

Decorator that sets DataFrame index if specified and the DataFrame is not empty.

## Internal Functions

These functions are used internally by the decorators:

### \_convert_time_values_in_dict

Converts Unix timestamp values in dictionaries to pandas datetime objects. Handles both seconds and milliseconds based on field naming conventions.

### \_convert_time_columns_in_df

Converts time columns in pandas DataFrames to datetime format. Automatically detects time columns by name patterns.

## Usage

These utilities are primarily used internally by Mt5DataClient methods through decorators:

```python
# Example of how decorators are applied internally
@detect_and_convert_time_to_datetime(skip_toggle="convert_time")
@set_index_if_possible(index_parameters="index_keys")
def some_method(self, convert_time: bool = True, index_keys: str | None = None):
    # Method implementation
    pass
```

## Time Conversion Rules

The time conversion follows these rules:

1. **Millisecond Timestamps**: Fields ending with `_msc` are converted using `pd.to_datetime(value, unit="ms")`
2. **Second Timestamps**: Fields named `time` or starting with `time_` are converted using `pd.to_datetime(value, unit="s")`
3. **Automatic Detection**: Conversion happens automatically unless explicitly disabled

## DataFrame Index Setting

The index setting decorator:

1. Only sets index if DataFrame is not empty
2. Uses the specified column name as index
3. Validates that the result is a DataFrame
4. Preserves original DataFrame if no index column specified

## Integration with Mt5DataClient

These utilities enable Mt5DataClient to provide user-friendly data:

```python
# Time values are automatically converted
df = client.get_symbols_as_df(convert_time=True)
# Returns DataFrame with datetime objects instead of Unix timestamps

# DataFrames can have custom indexes
df = client.copy_rates_from_as_df(
    symbol="EURUSD",
    timeframe=mt5.TIMEFRAME_H1,
    date_from=datetime.now(),
    count=100,
    index_keys="time"  # Sets 'time' column as index
)
```

## Design Philosophy

The utilities module follows these principles:

1. **Automatic Conversion**: Time values should be human-readable by default
2. **Opt-out Capability**: Users can disable conversion when needed
3. **Type Safety**: Decorators validate input and output types
4. **Non-intrusive**: Original data is never modified, only copies
5. **Consistent Behavior**: Same conversion rules across all methods

## Implementation Details

### Time Detection Patterns

- `time`: Base time field (seconds)
- `time_*`: Time-prefixed fields (seconds)
- `time_*_msc`: Millisecond timestamp fields

### Error Handling

- Invalid DataFrame types raise `TypeError`
- Empty DataFrames are returned as-is
- Non-time fields are ignored during conversion

## Performance Considerations

- Conversions only happen when requested
- Dictionary operations use shallow copies
- DataFrame operations use efficient pandas methods
- Decorators add minimal overhead
