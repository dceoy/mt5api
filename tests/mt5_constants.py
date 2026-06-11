"""Shared MetaTrader 5 constant definitions for tests."""

from __future__ import annotations

from enum import IntEnum


class Mt5Timeframe(IntEnum):
    """Test copy of MetaTrader5 timeframe constants."""

    TIMEFRAME_M1 = 1
    TIMEFRAME_M2 = 2
    TIMEFRAME_M3 = 3
    TIMEFRAME_M4 = 4
    TIMEFRAME_M5 = 5
    TIMEFRAME_M6 = 6
    TIMEFRAME_M10 = 10
    TIMEFRAME_M12 = 12
    TIMEFRAME_M15 = 15
    TIMEFRAME_M20 = 20
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H2 = 16386
    TIMEFRAME_H3 = 16387
    TIMEFRAME_H4 = 16388
    TIMEFRAME_H6 = 16390
    TIMEFRAME_H8 = 16392
    TIMEFRAME_H12 = 16396
    TIMEFRAME_D1 = 16408
    TIMEFRAME_W1 = 32769
    TIMEFRAME_MN1 = 49153


class Mt5CopyTicks(IntEnum):
    """Test copy of MetaTrader5 copy-ticks constants."""

    COPY_TICKS_INFO = 1
    COPY_TICKS_TRADE = 2
    COPY_TICKS_ALL = -1


class Mt5BookType(IntEnum):
    """Test copy of MetaTrader5 market book constants."""

    BOOK_TYPE_SELL = 1
    BOOK_TYPE_BUY = 2


class Mt5OrderType(IntEnum):
    """Test copy of MetaTrader5 order type constants."""

    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7
    ORDER_TYPE_CLOSE_BY = 8


MT5_CONSTANT_ENUMS: tuple[type[IntEnum], ...] = (
    Mt5Timeframe,
    Mt5CopyTicks,
    Mt5BookType,
    Mt5OrderType,
)


def install_mt5_constants(module: object) -> None:
    """Populate a mock MetaTrader5 module with shared constant definitions."""
    for enum_class in MT5_CONSTANT_ENUMS:
        for constant in enum_class:
            setattr(module, constant.name, int(constant))
