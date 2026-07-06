"""Pytest fixtures for API testing."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from mt5api.constants import API_KEY_HEADER_NAME, ENV_MT5API_SECRET_KEY
from tests.mt5_constants import (
    Mt5BookType,
    Mt5OrderType,
    install_mt5_constants,
)

if TYPE_CHECKING:
    from collections.abc import Generator

# Mock MetaTrader5 module before any imports
# This prevents ModuleNotFoundError on non-Windows systems
if "MetaTrader5" not in sys.modules:
    mock_mt5_module = Mock()
    mock_mt5_module.__name__ = "MetaTrader5"
    install_mt5_constants(mock_mt5_module)
    sys.modules["MetaTrader5"] = mock_mt5_module

# Set test API secret key before importing app
os.environ[ENV_MT5API_SECRET_KEY] = "test-api-key-12345"


@pytest.fixture
def mock_mt5_client() -> Mock:
    """Create a mock Mt5DataClient for testing.

    Returns:
        Mock Mt5DataClient with common methods mocked.
    """
    client = Mock()

    # Mock version method
    client.version_as_dict.return_value = {
        "mt5_terminal_version": "5.0.4321",
        "build": 4321,
        "build_release_date": "2024-01-01",
    }

    # Mock account info
    client.account_info_as_dict.return_value = {
        "login": 12345,
        "balance": 10000.0,
        "equity": 10500.0,
        "margin": 500.0,
        "free_margin": 10000.0,
        "profit": 500.0,
    }
    client.account_info_as_df.return_value = pd.DataFrame([
        client.account_info_as_dict.return_value
    ])

    # Mock terminal info
    client.terminal_info_as_dict.return_value = {
        "connected": True,
        "trade_allowed": True,
        "tradeapi_disabled": False,
        "email_enabled": True,
    }
    client.terminal_info_as_df.return_value = pd.DataFrame([
        client.terminal_info_as_dict.return_value
    ])

    # Mock symbol info
    client.symbol_info_as_dict.return_value = {
        "name": "EURUSD",
        "bid": 1.08500,
        "ask": 1.08520,
        "spread": 20,
        "volume_min": 0.01,
        "volume_max": 500.0,
    }
    client.symbol_info_as_df.return_value = pd.DataFrame([
        client.symbol_info_as_dict.return_value
    ])

    # Mock symbol tick
    client.symbol_info_tick_as_dict.return_value = {
        "time": 1704067200,
        "bid": 1.08500,
        "ask": 1.08520,
        "last": 1.08510,
        "volume": 100,
    }
    client.symbol_info_tick_as_df.return_value = pd.DataFrame([
        client.symbol_info_tick_as_dict.return_value
    ])

    # Mock symbols_get returning DataFrame
    client.symbols_get.return_value = pd.DataFrame([
        {"name": "EURUSD", "visible": True, "spread": 20},
        {"name": "GBPUSD", "visible": True, "spread": 25},
    ])
    client.symbols_get_as_df.return_value = client.symbols_get.return_value

    # Mock copy_rates_from returning DataFrame
    client.copy_rates_from.return_value = pd.DataFrame([
        {
            "time": 1704067200,
            "open": 1.08500,
            "high": 1.08600,
            "low": 1.08400,
            "close": 1.08550,
            "volume": 1000,
        },
        {
            "time": 1704070800,
            "open": 1.08550,
            "high": 1.08650,
            "low": 1.08450,
            "close": 1.08600,
            "volume": 1200,
        },
    ])
    client.copy_rates_from_as_df.return_value = client.copy_rates_from.return_value
    client.copy_rates_from_pos_as_df.return_value = client.copy_rates_from.return_value
    client.copy_rates_range_as_df.return_value = client.copy_rates_from.return_value

    # Mock copy_ticks_from returning DataFrame
    client.copy_ticks_from.return_value = pd.DataFrame([
        {
            "time": 1704067200,
            "bid": 1.08500,
            "ask": 1.08520,
            "last": 1.08510,
            "volume": 100,
        },
    ])
    client.copy_ticks_from_as_df.return_value = client.copy_ticks_from.return_value
    client.copy_ticks_range_as_df.return_value = client.copy_ticks_from.return_value

    # Mock market book returning DataFrame
    client.market_book_get_as_df.return_value = pd.DataFrame([
        {
            "type": int(Mt5BookType.BOOK_TYPE_SELL),
            "price": 1.08500,
            "volume": 1.0,
        },
        {
            "type": int(Mt5BookType.BOOK_TYPE_BUY),
            "price": 1.08520,
            "volume": 1.5,
        },
    ])

    # Mock positions_get returning DataFrame
    client.positions_get.return_value = pd.DataFrame([
        {
            "ticket": 123456,
            "symbol": "EURUSD",
            "volume": 0.10,
            "price_open": 1.08500,
            "price_current": 1.08600,
            "profit": 10.0,
        },
    ])
    client.positions_get_as_df.return_value = client.positions_get.return_value

    # Mock orders_get returning DataFrame
    client.orders_get.return_value = pd.DataFrame([
        {
            "ticket": 789012,
            "symbol": "GBPUSD",
            "type": int(Mt5OrderType.ORDER_TYPE_BUY_LIMIT),
            "volume": 0.10,
            "price_open": 1.25000,
        },
    ])
    client.orders_get_as_df.return_value = client.orders_get.return_value

    # Mock history methods returning DataFrames
    client.history_orders_get.return_value = pd.DataFrame([])
    client.history_deals_get.return_value = pd.DataFrame([])
    client.history_orders_get_as_df.return_value = pd.DataFrame([])
    client.history_deals_get_as_df.return_value = pd.DataFrame([])

    # Mock last error
    client.last_error_as_dict.return_value = {
        "error_code": 1,
        "error_description": "Success",
    }

    # Mock totals
    client.symbols_total.return_value = 100
    client.orders_total.return_value = 3
    client.positions_total.return_value = 5
    client.history_orders_total.return_value = 42
    client.history_deals_total.return_value = 37

    # Mock calculation methods
    client.order_calc_margin.return_value = 108.50
    client.order_calc_profit.return_value = 50.0

    # Mock trading write methods
    client.order_check_as_dict.return_value = {
        "retcode": 0,
        "balance": 10000.0,
        "equity": 10500.0,
        "profit": 0.0,
        "margin": 108.50,
        "margin_free": 10391.50,
        "margin_level": 9677.42,
        "comment": "Done",
        "request_action": 1,
        "request_symbol": "EURUSD",
        "request_volume": 0.1,
        "request_type": 0,
    }
    client.symbol_select.return_value = True
    client.market_book_add.return_value = True
    client.market_book_release.return_value = True

    return client


@pytest.fixture
def client(
    mock_mt5_client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with mocked MT5 client.

    Args:
        mock_mt5_client: Mocked Mt5DataClient fixture.
        monkeypatch: Pytest monkeypatch fixture for patching.

    Yields:
        FastAPI test client.
    """
    # Import after setting environment variable and mocking MetaTrader5
    from mt5api import dependencies  # noqa: PLC0415
    from mt5api.main import app  # noqa: PLC0415
    from mt5api.routers import health  # noqa: PLC0415

    # Patch get_mt5_client where it's called directly
    monkeypatch.setattr(health, "get_mt5_client", lambda: mock_mt5_client)

    # Clear any existing overrides
    app.dependency_overrides.clear()

    # Override dependencies for routes that use them
    app.dependency_overrides[dependencies.get_mt5_client] = lambda: mock_mt5_client
    # Don't override verify_api_key - let it work normally for auth tests

    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None

    with TestClient(app) as test_client:
        yield test_client

    app.state.active_market_book_subscriptions = set()
    app.state.market_book_cleanup_client = None


@pytest.fixture
def api_headers() -> dict[str, str]:
    """Get default API headers with authentication.

    Returns:
        Dictionary with X-API-Key header.
    """
    return {API_KEY_HEADER_NAME: "test-api-key-12345"}


@pytest.fixture(autouse=True)
def reset_mt5_client_singleton() -> Generator[None, None, None]:
    """Reset MT5 client singleton between tests.

    This fixture automatically runs before each test to ensure
    clean state.

    Yields:
        None
    """
    from mt5api import dependencies  # noqa: PLC0415

    # Reset singleton before test
    dependencies._mt5_client = None  # pyright: ignore[reportPrivateUsage]

    yield

    # Reset singleton after test
    dependencies._mt5_client = None  # pyright: ignore[reportPrivateUsage]
