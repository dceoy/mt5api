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
        1,
        5,
        15,
        30,
        16385,
        16388,
        16408,
        32769,
        49153,
    ]
    assert get_mt5_copy_ticks_examples() == [1, 2, 3]


def test_rates_from_request_accepts_mt5_timeframe_name() -> None:
    """Rates requests accept MT5 timeframe constant names."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": "TIMEFRAME_M1",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
    })

    assert request.timeframe == 1


def test_ticks_from_request_accepts_mt5_copy_ticks_name() -> None:
    """Tick requests accept MT5 COPY_TICKS constant names."""
    request = TicksFromRequest.model_validate({
        "symbol": "EURUSD",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
        "flags": "COPY_TICKS_ALL",
    })

    assert request.flags == 3


def test_rates_from_request_rejects_invalid_mt5_timeframe_type() -> None:
    """Rates requests reject non-string, non-integer timeframe values."""
    with pytest.raises(ValidationError, match="constant name or integer value"):
        RatesFromRequest.model_validate({
            "symbol": "EURUSD",
            "timeframe": [],
            "date_from": datetime(2024, 1, 1, tzinfo=UTC),
            "count": 10,
        })
