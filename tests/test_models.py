"""Tests for API request models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mt5api.models import (
    CalcMarginRequest,
    HistoryOrdersRequest,
    HistoryTotalRequest,
    RatesFromRequest,
    TicksFromRequest,
    TradeRequest,
    get_mt5_copy_ticks_examples,
    get_mt5_order_type_examples,
    get_mt5_timeframe_examples,
)
from tests.mt5_constants import Mt5CopyTicks, Mt5OrderType, Mt5Timeframe


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
        int(Mt5Timeframe.TIMEFRAME_M1),
        int(Mt5Timeframe.TIMEFRAME_M5),
        int(Mt5Timeframe.TIMEFRAME_M15),
        int(Mt5Timeframe.TIMEFRAME_M30),
        int(Mt5Timeframe.TIMEFRAME_H1),
        int(Mt5Timeframe.TIMEFRAME_H4),
        int(Mt5Timeframe.TIMEFRAME_D1),
        int(Mt5Timeframe.TIMEFRAME_W1),
        int(Mt5Timeframe.TIMEFRAME_MN1),
    ]
    assert get_mt5_copy_ticks_examples() == [
        int(Mt5CopyTicks.COPY_TICKS_INFO),
        int(Mt5CopyTicks.COPY_TICKS_TRADE),
        int(Mt5CopyTicks.COPY_TICKS_ALL),
    ]


@pytest.mark.parametrize(
    ("timeframe", "expected"),
    [
        ("TIMEFRAME_M1", int(Mt5Timeframe.TIMEFRAME_M1)),
        ("M1", int(Mt5Timeframe.TIMEFRAME_M1)),
        (int(Mt5Timeframe.TIMEFRAME_M1), int(Mt5Timeframe.TIMEFRAME_M1)),
        (str(int(Mt5Timeframe.TIMEFRAME_M1)), int(Mt5Timeframe.TIMEFRAME_M1)),
    ],
)
def test_rates_from_request_accepts_mt5_timeframe_inputs(
    timeframe: object,
    expected: int,
) -> None:
    """Rates requests accept official names, aliases, integers, and numeric strings."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": timeframe,
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
    })

    assert request.timeframe == expected


def test_rates_from_request_accepts_mt5_timeframe_name() -> None:
    """Rates requests accept MT5 timeframe constant names."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": "TIMEFRAME_M1",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
    })

    assert request.timeframe == int(Mt5Timeframe.TIMEFRAME_M1)


def test_rates_from_request_accepts_mt5_timeframe_integer_string() -> None:
    """Rates requests accept stringified MT5 timeframe integer values."""
    request = RatesFromRequest.model_validate({
        "symbol": "EURUSD",
        "timeframe": str(int(Mt5Timeframe.TIMEFRAME_M1)),
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
    })

    assert request.timeframe == int(Mt5Timeframe.TIMEFRAME_M1)


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ("COPY_TICKS_ALL", int(Mt5CopyTicks.COPY_TICKS_ALL)),
        ("ALL", int(Mt5CopyTicks.COPY_TICKS_ALL)),
        (int(Mt5CopyTicks.COPY_TICKS_INFO), int(Mt5CopyTicks.COPY_TICKS_INFO)),
        (str(int(Mt5CopyTicks.COPY_TICKS_TRADE)), int(Mt5CopyTicks.COPY_TICKS_TRADE)),
    ],
)
def test_ticks_from_request_accepts_mt5_copy_ticks_inputs(
    flags: object,
    expected: int,
) -> None:
    """Tick requests accept official names, aliases, integers, and numeric strings."""
    request = TicksFromRequest.model_validate({
        "symbol": "EURUSD",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
        "flags": flags,
    })

    assert request.flags == expected


def test_ticks_from_request_accepts_mt5_copy_ticks_name() -> None:
    """Tick requests accept MT5 COPY_TICKS constant names."""
    request = TicksFromRequest.model_validate({
        "symbol": "EURUSD",
        "date_from": datetime(2024, 1, 1, tzinfo=UTC),
        "count": 10,
        "flags": "COPY_TICKS_ALL",
    })

    assert request.flags == int(Mt5CopyTicks.COPY_TICKS_ALL)


@pytest.mark.parametrize(
    "timeframe",
    [True, 1.0, None, [], 99],
)
def test_rates_from_request_rejects_invalid_mt5_timeframe_values(
    timeframe: object,
) -> None:
    """Rates requests reject bool, float, None, objects, and unsupported integers."""
    with pytest.raises(ValidationError):
        RatesFromRequest.model_validate({
            "symbol": "EURUSD",
            "timeframe": timeframe,
            "date_from": datetime(2024, 1, 1, tzinfo=UTC),
            "count": 10,
        })


def test_rates_from_request_rejects_invalid_mt5_timeframe_type() -> None:
    """Rates requests reject non-string, non-integer timeframe values."""
    with pytest.raises(ValidationError, match="Invalid MT5 timeframe"):
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
        match="Unsupported MT5 COPY_TICKS flag value: 99",
    ):
        TicksFromRequest.model_validate({
            "symbol": "EURUSD",
            "date_from": datetime(2024, 1, 1, tzinfo=UTC),
            "count": 10,
            "flags": 99,
        })


def test_mt5_order_type_example_helpers_return_integer_examples() -> None:
    """MT5 ORDER_TYPE helpers expose integer example values."""
    assert get_mt5_order_type_examples() == [
        int(Mt5OrderType.ORDER_TYPE_BUY),
        int(Mt5OrderType.ORDER_TYPE_SELL),
    ]


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("ORDER_TYPE_BUY", int(Mt5OrderType.ORDER_TYPE_BUY)),
        ("BUY", int(Mt5OrderType.ORDER_TYPE_BUY)),
        (int(Mt5OrderType.ORDER_TYPE_SELL), int(Mt5OrderType.ORDER_TYPE_SELL)),
        (str(int(Mt5OrderType.ORDER_TYPE_SELL)), int(Mt5OrderType.ORDER_TYPE_SELL)),
    ],
)
def test_calc_margin_request_accepts_order_type_inputs(
    action: object,
    expected: int,
) -> None:
    """Calc margin requests accept official names, aliases, integers, and strings."""
    request = CalcMarginRequest.model_validate({
        "action": action,
        "symbol": "EURUSD",
        "volume": 0.1,
        "price": 1.085,
    })

    assert request.action == expected


def test_calc_margin_request_accepts_order_type_name() -> None:
    """Calc margin request accepts ORDER_TYPE constant names."""
    request = CalcMarginRequest.model_validate({
        "action": "ORDER_TYPE_BUY",
        "symbol": "EURUSD",
        "volume": 0.1,
        "price": 1.085,
    })

    assert request.action == int(Mt5OrderType.ORDER_TYPE_BUY)


def test_history_total_request_rejects_invalid_date_range() -> None:
    """History total request rejects date ranges where start >= end."""
    with pytest.raises(ValueError, match="date_from must be before date_to"):
        HistoryTotalRequest(
            date_from=datetime(2024, 1, 2, tzinfo=UTC),
            date_to=datetime(2024, 1, 1, tzinfo=UTC),
        )


def test_history_total_request_rejects_equal_dates() -> None:
    """History total request rejects equal start and end timestamps."""
    timestamp = datetime(2024, 1, 1, tzinfo=UTC)

    with pytest.raises(ValueError, match="date_from must be before date_to"):
        HistoryTotalRequest(date_from=timestamp, date_to=timestamp)


def test_trade_request_accepts_supported_optional_fields() -> None:
    """Trade requests should accept explicitly whitelisted optional MT5 fields."""
    request = TradeRequest.model_validate({
        "action": 1,
        "symbol": "EURUSD",
        "volume": 0.1,
        "type": "ORDER_TYPE_BUY",
        "price": 1.085,
        "deviation": 10,
        "type_filling": 1,
        "type_time": 0,
        "position": 123456,
        "comment": "validation-check",
    })

    assert request.deviation == 10
    assert request.type_filling == 1
    assert request.type_time == 0
    assert request.position == 123456
    assert request.comment == "validation-check"


def test_trade_request_rejects_unknown_field() -> None:
    """Trade requests should reject unknown extra fields."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TradeRequest.model_validate({
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.085,
            "unsupported": True,
        })


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (
            {
                "action": -1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 0,
                "price": 1.085,
            },
            "greater than or equal to 0",
        ),
        (
            {
                "action": 1,
                "symbol": "",
                "volume": 0.1,
                "type": 0,
                "price": 1.085,
            },
            "at least 1 character",
        ),
        (
            {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0,
                "type": 0,
                "price": 1.085,
            },
            "greater than 0",
        ),
        (
            {
                "action": 1,
                "symbol": "EURUSD",
                "volume": 0.1,
                "type": 99,
                "price": 1.085,
            },
            "Unsupported MT5 ORDER_TYPE value: 99",
        ),
    ],
)
def test_trade_request_rejects_invalid_core_fields(
    payload: dict[str, object],
    match: str,
) -> None:
    """Trade requests should validate core field constraints."""
    with pytest.raises(ValidationError, match=match):
        TradeRequest.model_validate(payload)
