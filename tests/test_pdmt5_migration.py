"""Regression tests for the pdmt5 >= 1.2.0 migration.

pdmt5 1.2.0 removed constant-introspection helpers (``list_*``/``get_*``)
from the package root; they remain available from ``pdmt5.constants``. These
tests guard against regressions in that migration: import-time schema
construction, unchanged OpenAPI schema content, unchanged parsing behavior,
and the dependency floor declared in package metadata.
"""

from __future__ import annotations

import ast
import importlib
import importlib.metadata
import sys
from datetime import UTC, datetime
from pathlib import Path

import pdmt5
import pytest
from pdmt5 import constants as pdmt5_constants

from mt5api import models
from mt5api.models import (
    CalcMarginRequest,
    RatesFromRequest,
    TicksFromRequest,
)

_TIMEFRAME_DESCRIPTION = (
    "MetaTrader5 TIMEFRAME constant. Accepts a constant name such as "
    "TIMEFRAME_M1, short aliases such as M1, or the corresponding integer value."
)
_COPY_TICKS_DESCRIPTION = (
    "MetaTrader5 COPY_TICKS constant. Accepts COPY_TICKS_INFO, "
    "COPY_TICKS_TRADE, COPY_TICKS_ALL, short aliases such as ALL, "
    "or the corresponding integer value."
)
_ORDER_TYPE_DESCRIPTION = (
    "MetaTrader5 ORDER_TYPE constant. Accepts a constant name such as "
    "ORDER_TYPE_BUY, short aliases such as BUY, or the corresponding integer value."
)


def test_mt5api_models_imports_successfully() -> None:
    """``import mt5api.models`` succeeds against the installed pdmt5."""
    reloaded = importlib.reload(sys.modules["mt5api.models"])
    assert reloaded is models


def test_removed_root_helpers_are_not_exposed_by_pdmt5() -> None:
    """pdmt5 1.2.0 no longer exposes introspection helpers at the root."""
    removed_names = (
        "get_timeframe_name",
        "get_timeframe_value",
        "get_copy_ticks_name",
        "get_copy_ticks_value",
        "get_order_type_name",
        "get_order_type_value",
        "list_timeframe_names",
        "list_timeframe_values",
        "list_copy_ticks_names",
        "list_copy_ticks_values",
        "list_order_type_names",
        "list_order_type_values",
    )
    for name in removed_names:
        assert not hasattr(pdmt5, name)


def test_removed_root_helpers_remain_available_from_constants() -> None:
    """The removed helpers remain public from ``pdmt5.constants``."""
    for name in (
        "list_timeframe_names",
        "list_timeframe_values",
        "list_copy_ticks_names",
        "list_copy_ticks_values",
        "list_order_type_names",
        "list_order_type_values",
    ):
        assert callable(getattr(pdmt5_constants, name))


def test_production_code_does_not_access_removed_pdmt5_root_helpers() -> None:
    """No production source accesses removed helpers via ``pdmt5.<name>``."""
    removed_prefixes = ("get_", "list_")
    package_dir = Path(models.__file__).resolve().parent
    for path in package_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "pdmt5"
                and node.attr.startswith(removed_prefixes)
            ):
                pytest.fail(f"{path}:{node.lineno} accesses pdmt5.{node.attr}")
            if isinstance(node, ast.ImportFrom) and node.module == "pdmt5":
                for alias in node.names:
                    assert not alias.name.startswith(removed_prefixes), (
                        f"{path}:{node.lineno} imports pdmt5.{alias.name}"
                    )


def test_timeframe_values_present_in_generated_schema() -> None:
    """Timeframe enum values and names remain present in the schema."""
    schema = RatesFromRequest.model_json_schema()
    timeframe_schema = schema["properties"]["timeframe"]
    assert timeframe_schema["description"] == _TIMEFRAME_DESCRIPTION
    name_enum = timeframe_schema["anyOf"][0]["enum"]
    value_enum = timeframe_schema["anyOf"][1]["enum"]
    assert "TIMEFRAME_M1" in name_enum
    assert "TIMEFRAME_D1" in name_enum
    assert 1 in value_enum
    assert 16408 in value_enum
    assert timeframe_schema["examples"] == [
        "TIMEFRAME_M1",
        "TIMEFRAME_M5",
        "TIMEFRAME_M15",
        "TIMEFRAME_M30",
        "TIMEFRAME_H1",
        "TIMEFRAME_H4",
        "TIMEFRAME_D1",
        "TIMEFRAME_W1",
        "TIMEFRAME_MN1",
    ]


def test_copy_ticks_values_present_in_generated_schema() -> None:
    """COPY_TICKS enum values and names remain present in the schema."""
    schema = TicksFromRequest.model_json_schema()
    flags_schema = schema["properties"]["flags"]
    assert flags_schema["description"] == _COPY_TICKS_DESCRIPTION
    name_enum = flags_schema["anyOf"][0]["enum"]
    value_enum = flags_schema["anyOf"][1]["enum"]
    assert {"COPY_TICKS_INFO", "COPY_TICKS_TRADE", "COPY_TICKS_ALL"} <= set(name_enum)
    assert {1, 2, -1} <= set(value_enum)
    assert flags_schema["examples"] == [
        "COPY_TICKS_INFO",
        "COPY_TICKS_TRADE",
        "COPY_TICKS_ALL",
    ]


def test_order_type_values_present_in_generated_schema() -> None:
    """ORDER_TYPE enum values and names remain present in the schema."""
    schema = CalcMarginRequest.model_json_schema()
    action_schema = schema["properties"]["action"]
    assert action_schema["description"] == _ORDER_TYPE_DESCRIPTION
    name_enum = action_schema["anyOf"][0]["enum"]
    value_enum = action_schema["anyOf"][1]["enum"]
    assert {"ORDER_TYPE_BUY", "ORDER_TYPE_SELL"} <= set(name_enum)
    assert {0, 1} <= set(value_enum)
    assert action_schema["examples"] == ["ORDER_TYPE_BUY", "ORDER_TYPE_SELL"]


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("M1", 1),
        ("TIMEFRAME_M1", 1),
        (1, 1),
        ("D1", 16408),
    ],
)
def test_timeframe_parsing_accepts_existing_aliases(
    alias: str | int, expected: int
) -> None:
    """Timeframe parsing accepts the same string aliases and integers."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": alias,
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 1,
    })
    assert request.timeframe == expected


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("ALL", -1),
        ("COPY_TICKS_ALL", -1),
        (-1, -1),
        ("INFO", 1),
    ],
)
def test_copy_ticks_parsing_accepts_existing_aliases(
    alias: str | int, expected: int
) -> None:
    """COPY_TICKS parsing accepts the same string aliases and integers."""
    request = TicksFromRequest.model_validate({
        "symbol": "EURUSD",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 1,
        "flags": alias,
    })
    assert request.flags == expected


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("BUY", 0),
        ("ORDER_TYPE_BUY", 0),
        (0, 0),
        ("SELL", 1),
    ],
)
def test_order_type_parsing_accepts_existing_aliases(
    alias: str | int, expected: int
) -> None:
    """ORDER_TYPE parsing accepts the same string aliases and integers."""
    request = CalcMarginRequest.model_validate({
        "action": alias,
        "symbol": "EURUSD",
        "volume": 1.0,
        "price": 1.1,
    })
    assert request.action == expected


def test_installed_package_metadata_requires_pdmt5_1_2_0() -> None:
    """Installed mt5api metadata declares a pdmt5 >= 1.2.0 requirement."""
    requires = importlib.metadata.requires("mt5api") or []
    pdmt5_requirements = [
        req for req in requires if req.split(";")[0].strip().startswith("pdmt5")
    ]
    assert pdmt5_requirements, "mt5api metadata does not declare a pdmt5 requirement"
    assert any(">=1.2.0" in req.replace(" ", "") for req in pdmt5_requirements), (
        pdmt5_requirements
    )
