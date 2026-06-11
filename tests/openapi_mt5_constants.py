"""Shared OpenAPI schema assertions for MT5 constant metadata."""

from __future__ import annotations

from typing import Any

from mt5api.models import (
    get_mt5_order_type_example_names,
    get_mt5_order_type_names,
    get_mt5_order_type_values,
)

ORDER_TYPE_DESCRIPTION = (
    "MetaTrader5 ORDER_TYPE constant. Accepts a constant name such as "
    "ORDER_TYPE_BUY, short aliases such as BUY, or the corresponding integer value."
)
VALID_ORDER_TYPE_NAMES = list(get_mt5_order_type_names())
VALID_ORDER_TYPE_VALUES = list(get_mt5_order_type_values())
ORDER_TYPE_EXAMPLES = get_mt5_order_type_example_names()


def assert_openapi_mt5_order_type_schema(schema: dict[str, Any]) -> None:
    """Assert an OpenAPI schema documents ORDER_TYPE names, values, and examples."""
    string_schema = next(
        member for member in schema["anyOf"] if member["type"] == "string"
    )
    integer_schema = next(
        member for member in schema["anyOf"] if member["type"] == "integer"
    )

    assert sorted(string_schema["enum"]) == sorted(VALID_ORDER_TYPE_NAMES)
    assert sorted(integer_schema["enum"]) == sorted(VALID_ORDER_TYPE_VALUES)
    assert schema["examples"] == ORDER_TYPE_EXAMPLES
    assert schema["description"] == ORDER_TYPE_DESCRIPTION
