"""Utility functions for the pdmt5 package."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable


def detect_and_convert_time_to_datetime(
    skip_toggle: str | None = None,
) -> Callable[..., Any]:
    """Decorator to convert time values/columns to datetime based on result type.

    Automatically detects result type and applies appropriate time conversion:
    - dict: converts time values in the dictionary
    - list: converts time values in each dictionary item
    - DataFrame: converts time columns

    Args:
        skip_toggle: Name of the parameter to skip conversion if set to False.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            result = func(*args, **kwargs)
            if skip_toggle and kwargs.get(skip_toggle):
                return result
            elif isinstance(result, dict):
                return _convert_time_values_in_dict(dictionary=result)
            elif isinstance(result, list):
                return [
                    (
                        _convert_time_values_in_dict(dictionary=d)
                        if isinstance(d, dict)
                        else d
                    )
                    for d in result
                ]
            elif isinstance(result, pd.DataFrame):
                return _convert_time_columns_in_df(result)
            else:
                return result

        return wrapper

    return decorator


def _convert_time_values_in_dict(dictionary: dict[str, Any]) -> dict[str, Any]:
    """Convert time values in a dictionary to datetime.

    Args:
        dictionary: Dictionary to convert.

    Returns:
        Dictionary with converted time values.
    """
    new_dict = dictionary.copy()
    for k, v in new_dict.items():
        if not isinstance(v, (int, float)):
            continue
        elif k.startswith("time_") and k.endswith("_msc"):
            new_dict[k] = pd.to_datetime(v, unit="ms")
        elif k == "time" or k.startswith("time_"):
            new_dict[k] = pd.to_datetime(v, unit="s")
    return new_dict


def _convert_time_columns_in_df(df: pd.DataFrame) -> pd.DataFrame:
    """Convert time columns in DataFrame to datetime.

    Args:
        df: DataFrame to convert.

    Returns:
        DataFrame with converted time columns.
    """
    new_df = df.copy()
    for c in new_df.columns:
        if c.startswith("time_") and c.endswith("_msc"):
            new_df[c] = pd.to_datetime(new_df[c], unit="ms")
        elif c == "time" or c.startswith("time_"):
            new_df[c] = pd.to_datetime(new_df[c], unit="s")
    return new_df


def set_index_if_possible(index_parameters: str | None = None) -> Callable[..., Any]:
    """Decorator to set index on DataFrame results if not empty.

    Args:
        index_parameters: Name of the parameter to use as index if provided.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            result = func(*args, **kwargs)
            if not isinstance(result, pd.DataFrame):
                error_message = (
                    f"Function {func.__name__} returned non-DataFrame result: "
                    f"{type(result).__name__}. Expected DataFrame."
                )
                raise TypeError(error_message)
            elif index_parameters and kwargs.get(index_parameters) and not result.empty:
                return result.set_index(kwargs[index_parameters])
            else:
                return result

        return wrapper

    return decorator
