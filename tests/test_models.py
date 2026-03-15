"""Tests for API request models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mt5api.models import (
    HistoryOrdersRequest,
    RatesFromRequest,
    TicksFromRequest,
    get_mt5_copy_ticks_examples,
    get_mt5_timeframe_examples,
)
from tests.mt5_constants import MT5_COPY_TICKS_VALUES, MT5_TIMEFRAME_VALUES


def test_history_request_requires_filters() -> None:
    """History requests must include date range or ticket/position."""
    with pytest.raises(ValueError, match="Either"):
        HistoryOrdersRequest()


def test_history_request_rejects_invalid_date_range() -> None:
    """History requests reject date ranges where start >= end."""
    with pytest.raises(ValueError, match="date_from must be before date_to"):
        HistoryOrdersRequest(
            date_from=datetime(2024, 1, 2, tzinfo=UTC),
            date_to=datetime(2024, 1, 1, tzinfo=UTC),
        )


def test_mt5_constant_example_helpers_return_integer_examples() -> None:
    """MT5 constant helpers expose integer example values for compatibility."""
    assert get_mt5_timeframe_examples() == [
        MT5_TIMEFRAME_VALUES[name]
        for name in (
            "TIMEFRAME_M1",
            "TIMEFRAME_M5",
            "TIMEFRAME_M15",
            "TIMEFRAME_M30",
            "TIMEFRAME_H1",
            "TIMEFRAME_H4",
            "TIMEFRAME_D1",
            "TIMEFRAME_W1",
            "TIMEFRAME_MN1",
        )
    ]
    assert get_mt5_copy_ticks_examples() == [
        MT5_COPY_TICKS_VALUES[name]
        for name in ("COPY_TICKS_INFO", "COPY_TICKS_TRADE", "COPY_TICKS_ALL")
    ]


def test_rates_from_request_accepts_mt5_timeframe_name() -> None:
    """Rates requests accept MT5 timeframe constant names."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": "TIMEFRAME_M1",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
    })

    assert request.timeframe == MT5_TIMEFRAME_VALUES["TIMEFRAME_M1"]


def test_rates_from_request_accepts_mt5_timeframe_integer_string() -> None:
    """Rates requests accept stringified MT5 timeframe integer values."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": str(MT5_TIMEFRAME_VALUES["TIMEFRAME_M1"]),
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
    })

    assert request.timeframe == MT5_TIMEFRAME_VALUES["TIMEFRAME_M1"]


def test_ticks_from_request_accepts_mt5_copy_ticks_name() -> None:
    """Tick requests accept MT5 COPY_TICKS constant names."""
    request = TicksFromRequest.model_validate({
        "symbol": "EURUSD",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
        "flags": "COPY_TICKS_ALL",
    })

    assert request.flags == MT5_COPY_TICKS_VALUES["COPY_TICKS_ALL"]


def test_rates_from_request_rejects_invalid_mt5_timeframe_type() -> None:
    """Rates requests reject non-string, non-integer timeframe values."""
    with pytest.raises(ValidationError, match="constant name or integer value"):
        RatesFromRequest.model_validate({
            "symbol": "EURUSD",
            "timeframe": [],
            "date_from": datetime(2024, 1, 1, tzinfo=UTC),
            "count": 10,
        })


def test_ticks_from_request_rejects_invalid_mt5_copy_ticks_value() -> None:
    """Tick requests reject unsupported MT5 COPY_TICKS integer values."""
    with pytest.raises(
        ValidationError,
        match="Unsupported metatrader5 copy_ticks constant value: 99",
    ):
        TicksFromRequest.model_validate({
            "symbol": "EURUSD",
            "date_from": datetime(2024, 1, 1, tzinfo=UTC),
            "count": 10,
            "flags": 99,
        })
