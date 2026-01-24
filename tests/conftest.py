"""Pytest fixtures for API testing."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

# Mock MetaTrader5 module before any imports
# This prevents ModuleNotFoundError on non-Windows systems
if "MetaTrader5" not in sys.modules:
    mock_mt5_module = Mock()
    mock_mt5_module.__name__ = "MetaTrader5"
    sys.modules["MetaTrader5"] = mock_mt5_module

# Set test API key before importing app
os.environ["MT5_API_KEY"] = "test-api-key-12345"


@pytest.fixture
def mock_mt5_client() -> Mock:
    """Create a mock Mt5DataClient for testing.

    Returns:
        Mock Mt5DataClient with common methods mocked.
    """
    client = Mock()

    # Mock version method
    client.version_as_dict.return_value = {
        "version": "5.0.4321",
        "build": 4321,
        "release_date": "2024-01-01",
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
        {"type": 1, "price": 1.08500, "volume": 1.0},
        {"type": 2, "price": 1.08520, "volume": 1.5},
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
            "type": 2,  # Buy limit
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

    return client


@pytest.fixture
def client(mock_mt5_client: Mock, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create FastAPI test client with mocked MT5 client.

    Args:
        mock_mt5_client: Mocked Mt5DataClient fixture.
        monkeypatch: Pytest monkeypatch fixture for patching.

    Returns:
        FastAPI test client.
    """
    # Import after setting environment variable and mocking MetaTrader5
    from pdmt5.api import dependencies  # noqa: PLC0415
    from pdmt5.api.main import app  # noqa: PLC0415
    from pdmt5.api.routers import health  # noqa: PLC0415

    # Patch get_mt5_client where it's called directly
    monkeypatch.setattr(health, "get_mt5_client", lambda: mock_mt5_client)

    # Clear any existing overrides
    app.dependency_overrides.clear()

    # Override dependencies for routes that use them
    app.dependency_overrides[dependencies.get_mt5_client] = lambda: mock_mt5_client
    # Don't override verify_api_key - let it work normally for auth tests

    # Create test client
    test_client = TestClient(app)

    return test_client


@pytest.fixture
def api_headers() -> dict[str, str]:
    """Get default API headers with authentication.

    Returns:
        Dictionary with X-API-Key header.
    """
    return {"X-API-Key": "test-api-key-12345"}


@pytest.fixture(autouse=True)
def reset_mt5_client_singleton() -> Generator[None, None, None]:
    """Reset MT5 client singleton between tests.

    This fixture automatically runs before each test to ensure
    clean state.

    Yields:
        None
    """
    from pdmt5.api import dependencies  # noqa: PLC0415

    # Reset singleton before test
    dependencies._mt5_client = None  # pyright: ignore[reportPrivateUsage]

    yield

    # Reset singleton after test
    dependencies._mt5_client = None  # pyright: ignore[reportPrivateUsage]
