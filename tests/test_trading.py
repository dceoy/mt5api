"""Tests for pdmt5.trading module."""

# pyright: reportPrivateUsage=false
# pyright: reportAttributeAccessIssue=false

from collections.abc import Generator
from types import ModuleType
from typing import Literal, NamedTuple

import numpy as np
import pandas as pd
import pytest
from pytest_mock import MockerFixture

from pdmt5.mt5 import Mt5RuntimeError
from pdmt5.trading import Mt5TradingClient, Mt5TradingError

# Rebuild models to ensure they are fully defined for testing
Mt5TradingClient.model_rebuild()


@pytest.fixture(autouse=True)
def mock_mt5_import(  # noqa: PLR0915
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
) -> Generator[ModuleType | None, None, None]:
    """Mock MetaTrader5 import for all tests.

    Yields:
        Mock object or None: Mock MetaTrader5 module for successful imports,
                            None for import error tests.
    """
    # Skip mocking for tests that explicitly test import errors
    if "initialize_import_error" in request.node.name:
        yield None
        return
    else:
        # Create a real module instance and add mock attributes to it
        mock_mt5 = ModuleType("mock_mt5")
        # Make it a MagicMock while preserving module type
        for attr in dir(mocker.MagicMock()):
            if not attr.startswith("__") or attr == "__call__":
                setattr(mock_mt5, attr, getattr(mocker.MagicMock(), attr))

        # Configure common mock attributes
        mock_mt5.initialize = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.shutdown = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.last_error = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.account_info = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.terminal_info = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.symbols_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.symbol_info = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.symbol_info_tick = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.positions_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_check = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_send = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_calc_margin = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.copy_rates_from_pos = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.copy_ticks_range = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.history_deals_get = mocker.MagicMock()  # type: ignore[attr-defined]

        # Trading-specific constants
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.ORDER_TYPE_SELL = 1
        mock_mt5.POSITION_TYPE_BUY = 0
        mock_mt5.POSITION_TYPE_SELL = 1
        mock_mt5.ORDER_FILLING_IOC = 1
        mock_mt5.ORDER_FILLING_FOK = 2
        mock_mt5.ORDER_FILLING_RETURN = 3
        mock_mt5.ORDER_TIME_GTC = 0

        # Trade return codes
        mock_mt5.TRADE_RETCODE_REQUOTE = 10004
        mock_mt5.TRADE_RETCODE_REJECT = 10006
        mock_mt5.TRADE_RETCODE_CANCEL = 10007
        mock_mt5.TRADE_RETCODE_PLACED = 10008
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.TRADE_RETCODE_DONE_PARTIAL = 10010
        mock_mt5.TRADE_RETCODE_ERROR = 10011
        mock_mt5.TRADE_RETCODE_TIMEOUT = 10012
        mock_mt5.TRADE_RETCODE_INVALID = 10013
        mock_mt5.TRADE_RETCODE_INVALID_VOLUME = 10014
        mock_mt5.TRADE_RETCODE_INVALID_PRICE = 10015
        mock_mt5.TRADE_RETCODE_INVALID_STOPS = 10016
        mock_mt5.TRADE_RETCODE_TRADE_DISABLED = 10017
        mock_mt5.TRADE_RETCODE_MARKET_CLOSED = 10018
        mock_mt5.TRADE_RETCODE_NO_MONEY = 10019
        mock_mt5.TRADE_RETCODE_PRICE_CHANGED = 10020
        mock_mt5.TRADE_RETCODE_PRICE_OFF = 10021
        mock_mt5.TRADE_RETCODE_INVALID_EXPIRATION = 10022
        mock_mt5.TRADE_RETCODE_ORDER_CHANGED = 10023
        mock_mt5.TRADE_RETCODE_TOO_MANY_REQUESTS = 10024
        mock_mt5.TRADE_RETCODE_NO_CHANGES = 10025
        mock_mt5.TRADE_RETCODE_SERVER_DISABLES_AT = 10026
        mock_mt5.TRADE_RETCODE_CLIENT_DISABLES_AT = 10027
        mock_mt5.TRADE_RETCODE_LOCKED = 10028
        mock_mt5.TRADE_RETCODE_FROZEN = 10029
        mock_mt5.TRADE_RETCODE_INVALID_FILL = 10030
        mock_mt5.TRADE_RETCODE_CONNECTION = 10031
        mock_mt5.TRADE_RETCODE_ONLY_REAL = 10032
        mock_mt5.TRADE_RETCODE_LIMIT_ORDERS = 10033
        mock_mt5.TRADE_RETCODE_LIMIT_VOLUME = 10034
        mock_mt5.TRADE_RETCODE_INVALID_ORDER = 10035
        mock_mt5.TRADE_RETCODE_POSITION_CLOSED = 10036
        mock_mt5.TRADE_RETCODE_INVALID_CLOSE_VOLUME = 10038
        mock_mt5.TRADE_RETCODE_CLOSE_ORDER_EXIST = 10039
        mock_mt5.TRADE_RETCODE_LIMIT_POSITIONS = 10040
        mock_mt5.TRADE_RETCODE_REJECT_CANCEL = 10041
        mock_mt5.TRADE_RETCODE_LONG_ONLY = 10042
        mock_mt5.TRADE_RETCODE_SHORT_ONLY = 10043
        mock_mt5.TRADE_RETCODE_CLOSE_ONLY = 10044
        mock_mt5.TRADE_RETCODE_FIFO_CLOSE = 10045
        mock_mt5.TRADE_RETCODE_HEDGE_PROHIBITED = 10046

        mock_mt5.RES_S_OK = 1
        mock_mt5.DEAL_TYPE_BUY = 0
        mock_mt5.DEAL_TYPE_SELL = 1

        yield mock_mt5


class MockPositionInfo(NamedTuple):
    """Mock position info structure."""

    ticket: int
    symbol: str
    volume: float
    type: int
    time: int
    identifier: int
    reason: int
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    magic: int
    comment: str
    external_id: str


class MockDealInfo(NamedTuple):
    """Mock deal info structure."""

    ticket: int
    type: int
    entry: bool
    time: int


@pytest.fixture
def mock_position_buy() -> MockPositionInfo:
    """Mock buy position."""
    return MockPositionInfo(
        ticket=12345,
        symbol="EURUSD",
        volume=0.1,
        type=0,  # POSITION_TYPE_BUY
        time=1234567890,
        identifier=12345,
        reason=0,
        price_open=1.2000,
        sl=0.0,
        tp=0.0,
        price_current=1.2050,
        swap=0.0,
        profit=5.0,
        magic=0,
        comment="test",
        external_id="",
    )


@pytest.fixture
def mock_position_sell() -> MockPositionInfo:
    """Mock sell position."""
    return MockPositionInfo(
        ticket=12346,
        symbol="GBPUSD",
        volume=0.2,
        type=1,  # POSITION_TYPE_SELL
        time=1234567890,
        identifier=12346,
        reason=0,
        price_open=1.3000,
        sl=0.0,
        tp=0.0,
        price_current=1.2950,
        swap=0.0,
        profit=10.0,
        magic=0,
        comment="test",
        external_id="",
    )


class TestMt5TradingError:
    """Tests for Mt5TradingError exception class."""

    def test_mt5_trading_error_inheritance(self) -> None:
        """Test that Mt5TradingError inherits from Mt5RuntimeError."""
        assert issubclass(Mt5TradingError, Mt5RuntimeError)

    def test_mt5_trading_error_creation(self) -> None:
        """Test Mt5TradingError creation with message."""
        message = "Trading operation failed"
        error = Mt5TradingError(message)
        assert str(error) == message
        assert isinstance(error, Mt5RuntimeError)

    def test_mt5_trading_error_empty_message(self) -> None:
        """Test Mt5TradingError creation with empty message."""
        error = Mt5TradingError("")
        assert not str(error)


class TestMt5TradingClient:
    """Tests for Mt5TradingClient class."""

    def test_client_initialization_default(self, mock_mt5_import: ModuleType) -> None:
        """Test client initialization with default parameters."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        # Order filling mode is now a parameter, not an attribute
        assert isinstance(client, Mt5TradingClient)

    def test_client_initialization_custom(self, mock_mt5_import: ModuleType) -> None:
        """Test client initialization with custom parameters."""
        # Order filling mode is now a parameter to methods, not a class attribute
        client = Mt5TradingClient(
            mt5=mock_mt5_import,
        )
        assert isinstance(client, Mt5TradingClient)

    def test_client_initialization_invalid_filling_mode(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test client initialization with invalid filling mode."""
        # Order filling mode is now a parameter to methods, not a class attribute
        client = Mt5TradingClient(mt5=mock_mt5_import)
        # Test that the method validates the parameter
        mock_mt5_import.initialize.return_value = True
        client.initialize()
        mock_mt5_import.positions_get.return_value = []
        # Should not raise as validation happens at method level
        result = client._fetch_and_close_position(order_filling_mode="IOC")  # type: ignore[arg-type]
        assert result == []

    def test_close_position_no_positions(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test close_position when no positions exist."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        result = client.close_open_positions("EURUSD")

        assert result == {"EURUSD": []}
        mock_mt5_import.positions_get.assert_called_once_with(symbol="EURUSD")

    def test_close_position_with_positions(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test close_position with existing positions."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "result": "success",
        }

        result = client.close_open_positions("EURUSD")

        assert len(result["EURUSD"]) == 1
        assert result["EURUSD"][0]["retcode"] == 10009
        mock_mt5_import.order_send.assert_called_once()

    def test_close_position_with_positions_dry_run(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test close_position with existing positions in dry run mode."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        result = client.close_open_positions("EURUSD", dry_run=True)

        assert len(result["EURUSD"]) == 1
        assert result["EURUSD"][0]["retcode"] == 0
        mock_mt5_import.order_check.assert_called_once()
        mock_mt5_import.order_send.assert_not_called()

    def test_close_position_with_dry_run_override(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test close_position with dry_run parameter override."""
        # Client initialized without dry_run
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        # Override with dry_run=True
        result = client.close_open_positions("EURUSD", dry_run=True)

        assert len(result["EURUSD"]) == 1
        assert result["EURUSD"][0]["retcode"] == 0
        # Should use order_check instead of order_send
        mock_mt5_import.order_check.assert_called_once()
        mock_mt5_import.order_send.assert_not_called()

    def test_close_position_with_real_mode_override(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test close_position with real mode override."""
        # Client initialized without dry_run
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "result": "send_success",
        }

        # Override with dry_run=False
        result = client.close_open_positions("EURUSD", dry_run=False)

        assert len(result["EURUSD"]) == 1
        assert result["EURUSD"][0]["retcode"] == 10009
        # Should use order_send instead of order_check
        mock_mt5_import.order_send.assert_called_once()
        mock_mt5_import.order_check.assert_not_called()

    def test_close_open_positions_all_symbols(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test close_open_positions for all symbols."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbols and positions
        mock_mt5_import.symbols_get.return_value = ["EURUSD", "GBPUSD"]
        mock_mt5_import.positions_get.return_value = []  # No positions

        result = client.close_open_positions()

        assert len(result) == 2
        assert "EURUSD" in result
        assert "GBPUSD" in result
        assert result["EURUSD"] == []
        assert result["GBPUSD"] == []

    def test_close_open_positions_specific_symbols(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test close_open_positions for specific symbols."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        result = client.close_open_positions(["EURUSD"])

        assert len(result) == 1
        assert "EURUSD" in result
        assert result["EURUSD"] == []

    def test_close_open_positions_tuple_input(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test close_open_positions with tuple input."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        result = client.close_open_positions(("EURUSD", "GBPUSD"))

        assert len(result) == 2
        assert "EURUSD" in result
        assert "GBPUSD" in result
        assert result["EURUSD"] == []
        assert result["GBPUSD"] == []

    def test_close_open_positions_with_kwargs(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test close_open_positions with additional kwargs."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "result": "success",
        }

        # Pass custom kwargs
        result = client.close_open_positions(
            "EURUSD", comment="custom_close", magic=12345
        )

        assert len(result["EURUSD"]) == 1
        assert result["EURUSD"][0]["retcode"] == 10009

        # Check that kwargs were passed through
        call_args = mock_mt5_import.order_send.call_args[0][0]
        assert call_args["comment"] == "custom_close"
        assert call_args["magic"] == 12345

    def test_close_open_positions_with_kwargs_and_dry_run(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test close_open_positions with additional kwargs and dry_run override."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        # Pass custom kwargs with dry_run override
        result = client.close_open_positions(
            "EURUSD", dry_run=True, comment="custom_close", magic=12345
        )

        assert len(result["EURUSD"]) == 1
        assert result["EURUSD"][0]["retcode"] == 0

        # Check that kwargs were passed through to order_check
        call_args = mock_mt5_import.order_check.call_args[0][0]
        assert call_args["comment"] == "custom_close"
        assert call_args["magic"] == 12345
        mock_mt5_import.order_send.assert_not_called()

    def test_send_or_check_order_dry_run_success(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test _send_or_check_order in dry run mode with success."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        # Mock successful order check
        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        result = client._send_or_check_order(request, dry_run=True)

        assert result["retcode"] == 0
        assert result["result"] == "check_success"
        mock_mt5_import.order_check.assert_called_once_with(request)

    def test_send_or_check_order_real_mode_success(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test _send_or_check_order in real mode with success."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        # Mock successful order send
        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "result": "send_success",
        }

        result = client._send_or_check_order(request)

        assert result["retcode"] == 10009
        assert result["result"] == "send_success"
        mock_mt5_import.order_send.assert_called_once_with(request)

    @pytest.mark.parametrize(
        ("retcode", "comment"),
        [
            (10017, "Trade disabled"),
            (10018, "Market closed"),
            (10025, "No changes"),
        ],
    )
    def test_send_or_check_order_non_error_retcodes(
        self, mock_mt5_import: ModuleType, retcode: int, comment: str
    ) -> None:
        """Test _send_or_check_order with non-error retcodes."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        mock_mt5_import.order_send.return_value.retcode = retcode
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": retcode,
            "comment": comment,
        }

        result = client._send_or_check_order(request)

        assert result["retcode"] == retcode

    def test_send_or_check_order_failure(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test _send_or_check_order with failure."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        # Mock failure response with error retcode
        mock_mt5_import.order_send.return_value.retcode = 10006
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10006,
            "comment": "Invalid request",
        }

        with pytest.raises(Mt5TradingError, match=r"order_send\(\) failed and aborted"):
            client._send_or_check_order(request, raise_on_error=True)

    def test_send_or_check_order_dry_run_failure(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test _send_or_check_order in dry run mode with failure."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        # Mock failure response with non-zero retcode for dry run
        mock_mt5_import.order_check.return_value.retcode = 10013
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 10013,
            "comment": "Invalid request",
        }

        with pytest.raises(
            Mt5TradingError, match=r"order_check\(\) failed and aborted"
        ):
            client._send_or_check_order(request, raise_on_error=True, dry_run=True)

    def test_send_or_check_order_dry_run_override(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test _send_or_check_order with dry_run parameter override."""
        # Client initialized without dry_run
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        # Mock successful order check
        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        # Override with dry_run=True
        result = client._send_or_check_order(request, dry_run=True)

        assert result["retcode"] == 0
        assert result["result"] == "check_success"
        # Should call order_check, not order_send
        mock_mt5_import.order_check.assert_called_once_with(request)
        mock_mt5_import.order_send.assert_not_called()

    def test_send_or_check_order_real_mode_override(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test _send_or_check_order with real mode override."""
        # Client initialized without dry_run
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        request = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 1,
        }

        # Mock successful order send
        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "result": "send_success",
        }

        # Override with dry_run=False
        result = client._send_or_check_order(request, dry_run=False)

        assert result["retcode"] == 10009
        assert result["result"] == "send_success"
        # Should call order_send, not order_check
        mock_mt5_import.order_send.assert_called_once_with(request)
        mock_mt5_import.order_check.assert_not_called()

    def test_place_market_order(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test place_market_order method."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock MT5 constants
        mock_mt5_import.ORDER_TYPE_BUY = 0
        mock_mt5_import.ORDER_FILLING_IOC = 1
        mock_mt5_import.ORDER_TIME_GTC = 0
        mock_mt5_import.TRADE_ACTION_DEAL = 1

        # Mock successful order send
        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "deal": 123456,
            "order": 789012,
        }

        result = client.place_market_order(
            symbol="EURUSD",
            volume=0.1,
            order_side="BUY",
            order_filling_mode="IOC",
            order_time_mode="GTC",
        )

        assert result["retcode"] == 10009
        assert result["deal"] == 123456
        assert result["order"] == 789012

        # Verify the request was built correctly
        expected_request = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,  # ORDER_TYPE_BUY
            "type_filling": 1,  # ORDER_FILLING_IOC
            "type_time": 0,  # ORDER_TIME_GTC
        }
        mock_mt5_import.order_send.assert_called_once_with(expected_request)

    def test_order_filling_mode_constants(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test that order filling mode constants are used correctly."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock positions
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009
        }

        # Call _fetch_and_close_position with FOK mode
        client._fetch_and_close_position("EURUSD", order_filling_mode="FOK")

        # Verify that ORDER_FILLING_FOK was used
        call_args = mock_mt5_import.order_send.call_args[0][0]
        assert call_args["type_filling"] == mock_mt5_import.ORDER_FILLING_FOK

    def test_position_type_handling(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
        mock_position_sell: MockPositionInfo,
    ) -> None:
        """Test that position types are handled correctly for closing."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Test buy position -> sell order
        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009
        }

        client.close_open_positions("EURUSD")

        # Buy position should result in sell order
        call_args = mock_mt5_import.order_send.call_args[0][0]
        assert call_args["type"] == mock_mt5_import.ORDER_TYPE_SELL

        # Test sell position -> buy order
        mock_mt5_import.positions_get.return_value = [mock_position_sell]

        mock_mt5_import.order_send.reset_mock()

        client.close_open_positions("GBPUSD")

        # Sell position should result in buy order
        call_args = mock_mt5_import.order_send.call_args[0][0]
        assert call_args["type"] == mock_mt5_import.ORDER_TYPE_BUY

    def test_fetch_and_close_position_with_dry_run(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
        mock_position_sell: MockPositionInfo,
    ) -> None:
        """Test _fetch_and_close_position with dry_run parameter."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Test with multiple positions and dry_run override
        mock_mt5_import.positions_get.return_value = [
            mock_position_buy,
            mock_position_sell,
        ]

        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        # Call internal method directly with dry_run=True
        result = client._fetch_and_close_position(symbol="EURUSD", dry_run=True)

        assert len(result) == 2
        assert all(r["retcode"] == 0 for r in result)
        assert mock_mt5_import.order_check.call_count == 2
        mock_mt5_import.order_send.assert_not_called()

    def test_fetch_and_close_position_inherits_instance_dry_run(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,
    ) -> None:
        """Test _fetch_and_close_position does not inherit dry_run from instance."""
        # Client initialized without dry_run
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        mock_mt5_import.positions_get.return_value = [mock_position_buy]

        mock_mt5_import.order_check.return_value.retcode = 0
        mock_mt5_import.order_check.return_value._asdict.return_value = {
            "retcode": 0,
            "result": "check_success",
        }

        # Call with dry_run=True explicitly
        result = client._fetch_and_close_position(symbol="EURUSD", dry_run=True)

        assert len(result) == 1
        assert result[0]["retcode"] == 0
        mock_mt5_import.order_check.assert_called_once()
        mock_mt5_import.order_send.assert_not_called()

    @pytest.mark.parametrize(
        ("order_side", "order_type_attr", "price_key", "expected_margin"),
        [
            ("BUY", "ORDER_TYPE_BUY", "ask", 100.5),
            ("SELL", "ORDER_TYPE_SELL", "bid", 99.8),
        ],
    )
    def test_calculate_minimum_order_margin_success(
        self,
        mock_mt5_import: ModuleType,
        order_side: Literal["BUY", "SELL"],
        order_type_attr: str,
        price_key: str,
        expected_margin: float,
    ) -> None:
        """Test successful calculation of minimum order margin."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "volume_min": 0.01,
            "name": "EURUSD",
        }

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "ask": 1.1000,
            "bid": 1.0998,
        }

        mock_mt5_import.order_calc_margin.return_value = expected_margin

        result = client.calculate_minimum_order_margin("EURUSD", order_side)

        assert result == {"volume": 0.01, "margin": expected_margin}
        tick_info = mock_mt5_import.symbol_info_tick.return_value._asdict.return_value
        mock_mt5_import.order_calc_margin.assert_called_once_with(
            getattr(mock_mt5_import, order_type_attr),
            "EURUSD",
            0.01,
            tick_info[price_key],
        )

    @pytest.mark.parametrize(
        ("order_side", "budget", "order_calc_margin_return", "expected_volume"),
        [
            ("BUY", 1000.0, 100.5, 0.09),
            ("SELL", 500.0, 99.8, 0.05),
        ],
    )
    def test_calculate_volume_by_margin_success(
        self,
        mock_mt5_import: ModuleType,
        order_side: Literal["BUY", "SELL"],
        budget: float,
        order_calc_margin_return: float,
        expected_volume: float,
    ) -> None:
        """Test successful calculation of volume by margin."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "volume_min": 0.01,
            "name": "EURUSD",
        }

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "ask": 1.1000,
            "bid": 1.0998,
        }

        mock_mt5_import.order_calc_margin.return_value = order_calc_margin_return

        result = client.calculate_volume_by_margin("EURUSD", budget, order_side)

        assert result == expected_volume

    def test_calculate_minimum_order_margin_no_margin(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test calculation when order_calc_margin returns zero."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "volume_min": 0.01,
            "name": "EURUSD",
        }

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "ask": 1.1000,
            "bid": 1.0998,
        }

        # Mock order_calc_margin to return 0.0 (no margin required)
        mock_mt5_import.order_calc_margin.return_value = 0.0

        result = client.calculate_minimum_order_margin("EURUSD", "BUY")

        assert result == {"volume": 0.01, "margin": 0.0}
        mock_mt5_import.order_calc_margin.assert_called_once_with(
            mock_mt5_import.ORDER_TYPE_BUY,
            "EURUSD",
            0.01,
            1.1000,
        )

    def test_calculate_volume_by_margin_zero_margin(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test calculation when minimum order margin is zero."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "volume_min": 0.01,
            "name": "EURUSD",
        }

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "ask": 1.1000,
            "bid": 1.0998,
        }

        # Mock order_calc_margin to return 0.0 (no margin required)
        mock_mt5_import.order_calc_margin.return_value = 0.0

        result = client.calculate_volume_by_margin("EURUSD", 1000.0, "BUY")

        # Should return 0.0 when margin is zero
        assert result == 0.0

    def test_calculate_spread_ratio(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test calculation of spread ratio."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "ask": 1.1002,
            "bid": 1.1000,
        }

        result = client.calculate_spread_ratio("EURUSD")

        # Expected calculation: (1.1002 - 1.1000) / (1.1002 + 1.1000) * 2
        expected = (1.1002 - 1.1000) / (1.1002 + 1.1000) * 2
        assert result == expected
        mock_mt5_import.symbol_info_tick.assert_called_once_with("EURUSD")

    def test_fetch_latest_rates_as_df_success(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test successful fetching of rate data as DataFrame."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock TIMEFRAME constant
        mock_mt5_import.TIMEFRAME_M1 = 1

        # Create structured array that mimics MT5 rates structure
        rates_dtype = np.dtype([
            ("time", "i8"),
            ("open", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("close", "f8"),
            ("tick_volume", "i8"),
            ("spread", "i4"),
            ("real_volume", "i8"),
        ])

        mock_rates_data = np.array(
            [
                (1234567890, 1.1000, 1.1010, 1.0990, 1.1005, 100, 2, 10000),
            ],
            dtype=rates_dtype,
        )

        mock_mt5_import.copy_rates_from_pos.return_value = mock_rates_data

        result = client.fetch_latest_rates_as_df("EURUSD", granularity="M1", count=10)

        assert result is not None
        mock_mt5_import.copy_rates_from_pos.assert_called_once_with(
            "EURUSD",  # symbol
            1,  # timeframe
            0,  # start_pos
            10,  # count
        )

    def test_fetch_latest_rates_as_df_invalid_granularity(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test fetching rate data with invalid granularity."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Ensure the attribute doesn't exist for invalid granularity
        if hasattr(mock_mt5_import, "TIMEFRAME_INVALID"):
            delattr(mock_mt5_import, "TIMEFRAME_INVALID")

        with pytest.raises(
            Mt5TradingError,
            match="MetaTrader5 does not support the given granularity: INVALID",
        ):
            client.fetch_latest_rates_as_df("EURUSD", granularity="INVALID")

    def test_fetch_latest_ticks_as_df(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test fetching tick data as DataFrame."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol tick info with time
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": 1234567890,
            "ask": 1.1002,
            "bid": 1.1000,
        }

        # Mock copy ticks flag
        mock_mt5_import.COPY_TICKS_ALL = 1

        # Create structured array that mimics MT5 ticks structure
        ticks_dtype = np.dtype([
            ("time", "i8"),
            ("bid", "f8"),
            ("ask", "f8"),
            ("last", "f8"),
            ("volume", "i8"),
            ("time_msc", "i8"),
            ("flags", "i4"),
            ("volume_real", "f8"),
        ])

        mock_ticks_data = np.array(
            [
                (1234567890, 1.1000, 1.1002, 1.1001, 100, 1234567890000, 0, 100.0),
            ],
            dtype=ticks_dtype,
        )

        mock_mt5_import.copy_ticks_range.return_value = mock_ticks_data

        result = client.fetch_latest_ticks_as_df("EURUSD", seconds=60)

        assert result is not None
        # Verify the method was called
        mock_mt5_import.symbol_info_tick.assert_called_once_with("EURUSD")

        # Verify copy_ticks_range was called with correct arguments
        call_args = mock_mt5_import.copy_ticks_range.call_args[0]
        assert call_args[0] == "EURUSD"  # symbol
        assert call_args[3] == 1  # flags (COPY_TICKS_ALL)

        # Verify result has the expected structure
        assert len(result) == 1
        # time_msc is likely the index, not a column
        assert "bid" in result.columns
        assert "ask" in result.columns
        assert "last" in result.columns
        assert "volume" in result.columns

    def test_collect_entry_deals_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test collecting entry deals as DataFrame."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": 1234567890,
        }

        # Create mock deal objects
        mock_deals = [
            # BUY, entry
            MockDealInfo(ticket=1001, type=0, entry=True, time=1234567890),
            # SELL, entry
            MockDealInfo(ticket=1002, type=1, entry=True, time=1234567891),
            # other type, entry
            MockDealInfo(ticket=1003, type=2, entry=True, time=1234567892),
            # BUY, not entry
            MockDealInfo(ticket=1004, type=0, entry=False, time=1234567893),
            # SELL, entry
            MockDealInfo(ticket=1005, type=1, entry=True, time=1234567894),
        ]

        # Mock history_deals_get to return the mock deals
        mock_mt5_import.history_deals_get.return_value = mock_deals

        result = client.collect_entry_deals_as_df("EURUSD", history_seconds=3600)

        # Verify symbol_info_tick was called
        mock_mt5_import.symbol_info_tick.assert_called_once_with("EURUSD")

        # Verify history_deals_get was called with correct parameters
        mock_mt5_import.history_deals_get.assert_called_once()
        call_args = mock_mt5_import.history_deals_get.call_args
        # Check positional args (date_from, date_to)
        assert len(call_args[0]) == 2
        date_from, date_to = call_args[0]
        # Compare timestamps to avoid timezone issues
        if isinstance(date_from, pd.Timestamp):
            date_from_ts = date_from.timestamp()
        else:
            date_from_ts = date_from.timestamp()
        if isinstance(date_to, pd.Timestamp):
            date_to_ts = date_to.timestamp()
        else:
            date_to_ts = date_to.timestamp()

        expected_from_ts = 1234567890 - 3600
        expected_to_ts = 1234567890 + 3600
        assert abs(date_from_ts - expected_from_ts) < 1  # Allow 1 second tolerance
        assert abs(date_to_ts - expected_to_ts) < 1  # Allow 1 second tolerance
        # Check group parameter
        assert call_args[1]["group"] == "*EURUSD*"

        # Verify filtered results - should only have entry deals with BUY/SELL types
        assert len(result) == 3  # tickets 1001, 1002, 1005
        assert 1001 in result.index  # entry=True, type=BUY
        assert 1002 in result.index  # entry=True, type=SELL
        assert 1003 not in result.index  # entry=True but type=2 (not BUY/SELL)
        assert 1004 not in result.index  # entry=False
        assert 1005 in result.index  # entry=True, type=SELL

    def test_collect_entry_deals_as_df_custom_parameters(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test collecting entry deals with custom parameters."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": 1234567890,
        }

        # Mock empty deals
        mock_mt5_import.history_deals_get.return_value = []

        result = client.collect_entry_deals_as_df(
            "GBPUSD", history_seconds=7200, index_keys="time"
        )

        # Verify parameters were passed through
        mock_mt5_import.history_deals_get.assert_called_once()
        call_args = mock_mt5_import.history_deals_get.call_args
        # Check positional args
        date_from, date_to = call_args[0]

        # Compare timestamps to avoid timezone issues
        if isinstance(date_from, pd.Timestamp):
            date_from_ts = date_from.timestamp()
        else:
            date_from_ts = date_from.timestamp()
        if isinstance(date_to, pd.Timestamp):
            date_to_ts = date_to.timestamp()
        else:
            date_to_ts = date_to.timestamp()

        expected_from_ts = 1234567890 - 7200
        expected_to_ts = 1234567890 + 7200
        assert abs(date_from_ts - expected_from_ts) < 1  # Allow 1 second tolerance
        assert abs(date_to_ts - expected_to_ts) < 1  # Allow 1 second tolerance
        # Check group parameter
        assert call_args[1]["group"] == "*GBPUSD*"

        # Result should be empty DataFrame
        assert len(result) == 0

    def test_collect_entry_deals_as_df_no_index(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test collecting entry deals without index."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": 1234567890,
        }

        # Create mock deal objects
        mock_deals = [
            # BUY, entry
            MockDealInfo(ticket=1001, type=0, entry=True, time=1234567890),
            # SELL, entry
            MockDealInfo(ticket=1002, type=1, entry=True, time=1234567891),
        ]

        # Mock history_deals_get to return the mock deals
        mock_mt5_import.history_deals_get.return_value = mock_deals

        result = client.collect_entry_deals_as_df(
            "USDJPY", history_seconds=1800, index_keys=None
        )

        # Verify results
        assert len(result) == 2
        # When index_keys is None, result should not have ticket as index
        assert result.index.name is None
        # Check that both deals are in the result
        assert 1001 in result["ticket"].to_numpy()
        assert 1002 in result["ticket"].to_numpy()

    def test_fetch_positions_with_metrics_as_df_empty(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test fetching positions with metrics when no positions exist."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        result = client.fetch_positions_with_metrics_as_df("EURUSD")

        # Should return empty DataFrame
        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_fetch_positions_with_metrics_as_df_with_positions(
        self,
        mock_mt5_import: ModuleType,
        mock_position_buy: MockPositionInfo,  # noqa: ARG002
        mocker: MockerFixture,
    ) -> None:
        """Test fetching positions with metrics when positions exist."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Create a mock position that returns the right data when converted
        mock_position = mocker.MagicMock()
        mock_position._asdict.return_value = {
            "ticket": 12345,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,  # POSITION_TYPE_BUY
            "time": 1234567890,  # This will be converted by decorator
            "price_open": 1.2,
            "price_current": 1.205,
            "profit": 5.0,
            "sl": 0.0,
            "tp": 0.0,
            "identifier": 12345,
            "reason": 0,
            "swap": 0.0,
            "magic": 0,
            "comment": "test",
            "external_id": "",
        }
        mock_mt5_import.positions_get.return_value = [mock_position]

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": pd.Timestamp(
                "2009-02-14 00:31:30"
            ),  # tz-naive to match decorated positions
            "ask": 1.1002,
            "bid": 1.1000,
        }

        # Mock order calc margin
        mock_mt5_import.order_calc_margin.return_value = 1000.0

        result = client.fetch_positions_with_metrics_as_df("EURUSD")

        # Verify DataFrame is not empty and has expected columns
        assert not result.empty
        assert isinstance(result, pd.DataFrame)
        assert "elapsed_seconds" in result.columns
        assert "underlier_profit_ratio" in result.columns
        assert "buy" in result.columns
        assert "sell" in result.columns
        assert "margin" in result.columns
        assert "signed_volume" in result.columns
        assert "signed_margin" in result.columns

        # Verify calculations
        row = result.iloc[0]
        assert row["buy"]  # mock_position_buy has type=0 (BUY)
        assert not row["sell"]
        assert row["margin"] == 100.0  # 0.1 volume * 1000 margin
        assert row["signed_volume"] == 0.1  # buy position has positive volume
        assert row["signed_margin"] == 100.0  # buy position has positive margin

        # Verify order_calc_margin was called twice (ask and bid)
        assert mock_mt5_import.order_calc_margin.call_count == 2

    def test_calculate_new_position_margin_ratio_no_equity(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test calculating margin ratio when account has no equity."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock account info with zero equity
        mock_mt5_import.account_info.return_value._asdict.return_value = {
            "equity": 0.0,
        }

        result = client.calculate_new_position_margin_ratio(
            symbol="EURUSD", new_position_side="BUY", new_position_volume=0.1
        )

        assert result == 0.0

    def test_calculate_new_position_margin_ratio_buy_position(
        self, mock_mt5_import: ModuleType, mocker: MockerFixture
    ) -> None:
        """Test calculating margin ratio for a new buy position."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock account info
        mock_mt5_import.account_info.return_value._asdict.return_value = {
            "equity": 10000.0,
        }

        # Mock existing positions
        mock_position = mocker.MagicMock()
        mock_position._asdict.return_value = {
            "ticket": 12345,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,  # POSITION_TYPE_BUY
            "time": 1234567890,
            "price_open": 1.2,
            "price_current": 1.205,
            "profit": 5.0,
            "sl": 0.0,
            "tp": 0.0,
            "identifier": 12345,
            "reason": 0,
            "swap": 0.0,
            "magic": 0,
            "comment": "test",
            "external_id": "",
        }
        mock_mt5_import.positions_get.return_value = [mock_position]

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": pd.Timestamp("2009-02-14 00:31:30"),
            "ask": 1.1002,
            "bid": 1.1000,
        }

        # Mock order calc margin
        mock_mt5_import.order_calc_margin.return_value = 1000.0

        result = client.calculate_new_position_margin_ratio(
            symbol="EURUSD", new_position_side="BUY", new_position_volume=0.1
        )

        # Should return (new_margin + current_margin) / equity
        # current_margin = 100.0 (from position), new_margin = 1000.0
        expected_ratio = abs((1000.0 + 100.0) / 10000.0)
        assert result == expected_ratio

    def test_calculate_new_position_margin_ratio_sell_position(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test calculating margin ratio for a new sell position."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock account info
        mock_mt5_import.account_info.return_value._asdict.return_value = {
            "equity": 10000.0,
        }

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": pd.Timestamp("2009-02-14 00:31:30"),
            "ask": 1.1002,
            "bid": 1.1000,
        }

        # Mock order calc margin
        mock_mt5_import.order_calc_margin.return_value = 1000.0

        result = client.calculate_new_position_margin_ratio(
            symbol="EURUSD", new_position_side="SELL", new_position_volume=0.1
        )

        # Should return abs(-new_margin / equity) for sell
        expected_ratio = abs(-1000.0 / 10000.0)
        assert result == expected_ratio

    def test_calculate_new_position_margin_ratio_zero_volume(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test calculating margin ratio with zero volume."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock account info
        mock_mt5_import.account_info.return_value._asdict.return_value = {
            "equity": 10000.0,
        }

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": pd.Timestamp("2009-02-14 00:31:30"),
            "ask": 1.1002,
            "bid": 1.1000,
        }

        result = client.calculate_new_position_margin_ratio(
            symbol="EURUSD", new_position_side="BUY", new_position_volume=0
        )

        # Should return 0 since new_position_volume is 0
        assert result == 0.0

    def test_calculate_new_position_margin_ratio_invalid_side(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test calculating margin ratio with invalid side."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock account info
        mock_mt5_import.account_info.return_value._asdict.return_value = {
            "equity": 10000.0,
        }

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": pd.Timestamp("2009-02-14 00:31:30"),
            "ask": 1.1002,
            "bid": 1.1000,
        }

        result = client.calculate_new_position_margin_ratio(
            symbol="EURUSD", new_position_side=None, new_position_volume=0.1
        )

        # Should return 0 since side is invalid
        assert result == 0.0

    def test_calculate_new_position_margin_ratio_invalid_side_string(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test calculating margin ratio with invalid side string."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock account info
        mock_mt5_import.account_info.return_value._asdict.return_value = {
            "equity": 10000.0,
        }

        # Mock empty positions
        mock_mt5_import.positions_get.return_value = []

        # Mock symbol tick info
        mock_mt5_import.symbol_info_tick.return_value._asdict.return_value = {
            "time": pd.Timestamp("2009-02-14 00:31:30"),
            "ask": 1.1002,
            "bid": 1.1000,
        }

        result = client.calculate_new_position_margin_ratio(
            symbol="EURUSD",
            new_position_side="INVALID",  # type: ignore[arg-type]
            new_position_volume=0.1,
        )

        # Should return 0 since side is invalid string
        assert result == 0.0

    def test_update_sltp_for_open_positions(self, mock_mt5_import: ModuleType) -> None:
        """Test update_sltp_for_open_positions method."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock MT5 constants
        mock_mt5_import.TRADE_ACTION_SLTP = 6

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "digits": 5,
        }

        # Mock positions for the symbol
        mock_position = MockPositionInfo(
            ticket=123456,
            time=123456789,
            type=0,  # buy
            magic=0,
            identifier=123456,
            reason=0,
            volume=0.1,
            price_open=1.1000,
            sl=1.0900,
            tp=1.1100,
            price_current=1.1050,
            swap=0.0,
            profit=50.0,
            symbol="EURUSD",
            comment="test",
            external_id="",
        )
        mock_mt5_import.positions_get.return_value = [mock_position]

        # Mock successful order send
        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "deal": 0,
            "order": 789012,
        }

        result = client.update_sltp_for_open_positions(
            symbol="EURUSD",
            tickets=[123456],
            stop_loss=1.0950,
            take_profit=1.1050,
        )

        # Now returns a list of dictionaries
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["retcode"] == 10009
        assert result[0]["order"] == 789012

    def test_update_sltp_for_open_positions_no_positions(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test update_sltp_for_open_positions when no positions exist for symbol."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock empty positions result
        mock_mt5_import.positions_get.return_value = []

        result = client.update_sltp_for_open_positions(
            symbol="EURUSD",
            tickets=[123456],
            stop_loss=1.0950,
            take_profit=1.1050,
        )

        # Should return empty list and log warning
        assert result == []
        # Verify positions_get was called with correct symbol
        mock_mt5_import.positions_get.assert_called_with(symbol="EURUSD")

    def test_update_sltp_for_open_positions_no_matching_tickets(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test update_sltp_for_open_positions when positions exist but no tickets match."""  # noqa: E501
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock MT5 constants
        mock_mt5_import.TRADE_ACTION_SLTP = 6

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "digits": 5,
        }

        # Mock positions with different tickets
        mock_position = MockPositionInfo(
            ticket=999999,  # Different ticket
            time=123456789,
            type=0,  # buy
            magic=0,
            identifier=999999,
            reason=0,
            volume=0.1,
            price_open=1.1000,
            sl=1.0900,
            tp=1.1100,
            price_current=1.1050,
            swap=0.0,
            profit=50.0,
            symbol="EURUSD",
            comment="test",
            external_id="",
        )
        mock_mt5_import.positions_get.return_value = [mock_position]

        result = client.update_sltp_for_open_positions(
            symbol="EURUSD",
            tickets=[123456],  # This ticket doesn't exist
            stop_loss=1.0950,
            take_profit=1.1050,
        )

        # Should return empty list and log warning
        assert result == []

    def test_update_sltp_for_open_positions_same_sltp_values(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test update_sltp_for_open_positions when SL/TP values are already the same."""  # noqa: E501
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock MT5 constants
        mock_mt5_import.TRADE_ACTION_SLTP = 6

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "digits": 5,
        }

        # Mock positions with same SL/TP as requested
        mock_position = MockPositionInfo(
            ticket=123456,
            time=123456789,
            type=0,  # buy
            magic=0,
            identifier=123456,
            reason=0,
            volume=0.1,
            price_open=1.1000,
            sl=1.0950,  # Same as requested stop_loss
            tp=1.1050,  # Same as requested take_profit
            price_current=1.1050,
            swap=0.0,
            profit=50.0,
            symbol="EURUSD",
            comment="test",
            external_id="",
        )
        mock_mt5_import.positions_get.return_value = [mock_position]

        result = client.update_sltp_for_open_positions(
            symbol="EURUSD",
            tickets=[123456],
            stop_loss=1.0950,  # Same as position's sl
            take_profit=1.1050,  # Same as position's tp
        )

        # Should return empty list since no update is needed
        assert result == []
        # Verify order_send was NOT called
        mock_mt5_import.order_send.assert_not_called()

    def test_update_sltp_for_open_positions_no_tickets(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test update_sltp_for_open_positions without specifying tickets."""
        client = Mt5TradingClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        client.initialize()

        # Mock MT5 constants
        mock_mt5_import.TRADE_ACTION_SLTP = 6

        # Mock symbol info
        mock_mt5_import.symbol_info.return_value._asdict.return_value = {
            "digits": 5,
        }

        # Mock positions for the symbol
        mock_position1 = MockPositionInfo(
            ticket=123456,
            time=123456789,
            type=0,  # buy
            magic=0,
            identifier=123456,
            reason=0,
            volume=0.1,
            price_open=1.1000,
            sl=1.0900,
            tp=1.1100,
            price_current=1.1050,
            swap=0.0,
            profit=50.0,
            symbol="EURUSD",
            comment="test",
            external_id="",
        )
        mock_position2 = MockPositionInfo(
            ticket=654321,
            time=123456789,
            type=1,  # sell
            magic=0,
            identifier=654321,
            reason=0,
            volume=0.2,
            price_open=1.1050,
            sl=1.1150,
            tp=1.0950,
            price_current=1.1050,
            swap=0.0,
            profit=-20.0,
            symbol="EURUSD",
            comment="test2",
            external_id="",
        )
        mock_mt5_import.positions_get.return_value = [mock_position1, mock_position2]

        # Mock successful order send
        mock_mt5_import.order_send.return_value.retcode = 10009
        mock_mt5_import.order_send.return_value._asdict.return_value = {
            "retcode": 10009,
            "deal": 0,
            "order": 789012,
        }

        # Call without tickets to update all positions
        result = client.update_sltp_for_open_positions(
            symbol="EURUSD",
            tickets=None,  # No tickets specified
            stop_loss=1.0950,
            take_profit=1.1050,
        )

        # Should return results for both positions
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(r["retcode"] == 10009 for r in result)

    def test_mt5_successful_trade_retcodes_property(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test mt5_successful_trade_retcodes property returns correct set of codes."""
        client = Mt5TradingClient(mt5=mock_mt5_import)

        # Get the property value
        retcodes = client.mt5_successful_trade_retcodes

        # Verify it's a set
        assert isinstance(retcodes, set)

        # Verify the expected codes are present
        assert retcodes == {
            mock_mt5_import.TRADE_RETCODE_PLACED,  # 10008
            mock_mt5_import.TRADE_RETCODE_DONE,  # 10009
            mock_mt5_import.TRADE_RETCODE_DONE_PARTIAL,  # 10010
        }

    def test_mt5_failed_trade_retcodes_property(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test mt5_failed_trade_retcodes property returns correct set of codes."""
        client = Mt5TradingClient(mt5=mock_mt5_import)

        # Get the property value
        retcodes = client.mt5_failed_trade_retcodes

        # Verify it's a set
        assert isinstance(retcodes, set)

        # Verify it contains the expected codes
        expected_codes = {
            mock_mt5_import.TRADE_RETCODE_REQUOTE,  # 10004
            mock_mt5_import.TRADE_RETCODE_REJECT,  # 10006
            mock_mt5_import.TRADE_RETCODE_CANCEL,  # 10007
            mock_mt5_import.TRADE_RETCODE_ERROR,  # 10011
            mock_mt5_import.TRADE_RETCODE_TIMEOUT,  # 10012
            mock_mt5_import.TRADE_RETCODE_INVALID,  # 10013
            mock_mt5_import.TRADE_RETCODE_INVALID_VOLUME,  # 10014
            mock_mt5_import.TRADE_RETCODE_INVALID_PRICE,  # 10015
            mock_mt5_import.TRADE_RETCODE_INVALID_STOPS,  # 10016
            mock_mt5_import.TRADE_RETCODE_TRADE_DISABLED,  # 10017
            mock_mt5_import.TRADE_RETCODE_MARKET_CLOSED,  # 10018
            mock_mt5_import.TRADE_RETCODE_NO_MONEY,  # 10019
            mock_mt5_import.TRADE_RETCODE_PRICE_CHANGED,  # 10020
            mock_mt5_import.TRADE_RETCODE_PRICE_OFF,  # 10021
            mock_mt5_import.TRADE_RETCODE_INVALID_EXPIRATION,  # 10022
            mock_mt5_import.TRADE_RETCODE_ORDER_CHANGED,  # 10023
            mock_mt5_import.TRADE_RETCODE_TOO_MANY_REQUESTS,  # 10024
            mock_mt5_import.TRADE_RETCODE_NO_CHANGES,  # 10025
            mock_mt5_import.TRADE_RETCODE_SERVER_DISABLES_AT,  # 10026
            mock_mt5_import.TRADE_RETCODE_CLIENT_DISABLES_AT,  # 10027
            mock_mt5_import.TRADE_RETCODE_LOCKED,  # 10028
            mock_mt5_import.TRADE_RETCODE_FROZEN,  # 10029
            mock_mt5_import.TRADE_RETCODE_INVALID_FILL,  # 10030
            mock_mt5_import.TRADE_RETCODE_CONNECTION,  # 10031
            mock_mt5_import.TRADE_RETCODE_ONLY_REAL,  # 10032
            mock_mt5_import.TRADE_RETCODE_LIMIT_ORDERS,  # 10033
            mock_mt5_import.TRADE_RETCODE_LIMIT_VOLUME,  # 10034
            mock_mt5_import.TRADE_RETCODE_INVALID_ORDER,  # 10035
            mock_mt5_import.TRADE_RETCODE_POSITION_CLOSED,  # 10036
            mock_mt5_import.TRADE_RETCODE_INVALID_CLOSE_VOLUME,  # 10038
            mock_mt5_import.TRADE_RETCODE_CLOSE_ORDER_EXIST,  # 10039
            mock_mt5_import.TRADE_RETCODE_LIMIT_POSITIONS,  # 10040
            mock_mt5_import.TRADE_RETCODE_REJECT_CANCEL,  # 10041
            mock_mt5_import.TRADE_RETCODE_LONG_ONLY,  # 10042
            mock_mt5_import.TRADE_RETCODE_SHORT_ONLY,  # 10043
            mock_mt5_import.TRADE_RETCODE_CLOSE_ONLY,  # 10044
            mock_mt5_import.TRADE_RETCODE_FIFO_CLOSE,  # 10045
            mock_mt5_import.TRADE_RETCODE_HEDGE_PROHIBITED,  # 10046
        }

        # Verify all expected codes are present
        assert retcodes == expected_codes
