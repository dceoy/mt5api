"""Tests for pdmt5.dataframe module."""

# pyright: reportPrivateUsage=false
# pyright: reportAttributeAccessIssue=false

from collections.abc import Generator
from datetime import UTC, datetime
from types import ModuleType
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from pdmt5.dataframe import Mt5Config, Mt5DataClient
from pdmt5.mt5 import Mt5Client, Mt5RuntimeError
from pdmt5.utils import (
    detect_and_convert_time_to_datetime,
)

# Rebuild models to ensure they are fully defined for testing
Mt5DataClient.model_rebuild()


@pytest.fixture(autouse=True)
def mock_mt5_import(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
) -> Generator[ModuleType | None, None, None]:
    """Mock MetaTrader5 import for all tests.

    Yields:
        Mock object or None: Mock MetaTrader5 module for successful imports,
                            None for import error tests.
    """
    # Skip mocking for tests that explicitly test import errors
    if (
        "initialize_import_error" in request.node.name
        or "test_error_handling_without_mt5" in request.node.name
    ):
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
        mock_mt5.copy_rates_from = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.copy_ticks_from = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.copy_rates_from_pos = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.copy_rates_range = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.copy_ticks_range = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.symbol_info_tick = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.orders_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.positions_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.history_deals_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.history_orders_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.login = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_check = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_send = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.orders_total = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.positions_total = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.history_orders_total = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.history_deals_total = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_calc_margin = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.order_calc_profit = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.version = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.symbols_total = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.symbol_select = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.market_book_add = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.market_book_release = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.market_book_get = mocker.MagicMock()  # type: ignore[attr-defined]
        mock_mt5.RES_S_OK = 1
        yield mock_mt5


class MockAccountInfo(NamedTuple):
    """Mock account info structure."""

    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_mode: int
    currency_digits: int
    fifo_close: bool
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    margin_so_call: float
    margin_so_so: float
    margin_initial: float
    margin_maintenance: float
    assets: float
    liabilities: float
    commission_blocked: float
    name: str
    server: str
    currency: str
    company: str


class MockTerminalInfo(NamedTuple):
    """Mock terminal info structure."""

    community_account: bool
    community_connection: bool
    connected: bool
    dlls_allowed: bool
    trade_allowed: bool
    tradeapi_disabled: bool
    email_enabled: bool
    ftp_enabled: bool
    notifications_enabled: bool
    mqid: bool
    build: int
    maxbars: int
    codepage: int
    ping_last: int
    community_balance: int
    retransmission: float
    company: str
    name: str
    language: int
    path: str
    data_path: str
    commondata_path: str


class MockSymbolInfo(NamedTuple):
    """Mock symbol info structure."""

    custom: bool
    chart_mode: int
    select: bool
    visible: bool
    session_deals: int
    session_buy_orders: int
    session_sell_orders: int
    volume: int
    volumehigh: int
    volumelow: int
    time: int
    digits: int
    spread: int
    spread_float: bool
    ticks_bookdepth: int
    trade_calc_mode: int
    trade_mode: int
    start_time: int
    expiration_time: int
    trade_stops_level: int
    trade_freeze_level: int
    trade_exemode: int
    swap_mode: int
    swap_rollover3days: int
    margin_hedged_use_leg: bool
    expiration_mode: int
    filling_mode: int
    order_mode: int
    order_gtc_mode: int
    option_mode: int
    option_right: int
    bid: float
    bidlow: float
    bidhigh: float
    ask: float
    asklow: float
    askhigh: float
    last: float
    lastlow: float
    lasthigh: float
    volume_real: float
    volumehigh_real: float
    volumelow_real: float
    option_strike: float
    point: float
    trade_tick_value: float
    trade_tick_value_profit: float
    trade_tick_value_loss: float
    trade_tick_size: float
    trade_contract_size: float
    trade_accrued_interest: float
    trade_face_value: float
    trade_liquidity_rate: float
    volume_min: float
    volume_max: float
    volume_step: float
    volume_limit: float
    swap_long: float
    swap_short: float
    margin_initial: float
    margin_maintenance: float
    session_volume: float
    session_turnover: float
    session_interest: float
    session_buy_orders_volume: float
    session_sell_orders_volume: float
    session_open: float
    session_close: float
    session_aw: float
    session_price_settlement: float
    session_price_limit_min: float
    session_price_limit_max: float
    margin_hedged: float
    price_change: float
    price_volatility: float
    price_theoretical: float
    price_greeks_delta: float
    price_greeks_theta: float
    price_greeks_gamma: float
    price_greeks_vega: float
    price_greeks_rho: float
    price_greeks_omega: float
    price_sensitivity: float
    basis: str
    category: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    bank: str
    description: str
    exchange: str
    formula: str
    isin: str
    name: str
    page: str
    path: str


class MockTick(NamedTuple):
    """Mock tick structure."""

    time: int
    bid: float
    ask: float
    last: float
    volume: int
    time_msc: int
    flags: int
    volume_real: float


class MockRate(NamedTuple):
    """Mock rate structure."""

    time: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class MockOrder(NamedTuple):
    """Mock order structure."""

    ticket: int
    time_setup: int
    time_setup_msc: int
    time_done: int
    time_done_msc: int
    time_expiration: int
    type: int
    type_time: int
    type_filling: int
    state: int
    magic: int
    position_id: int
    position_by_id: int
    reason: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    price_stoplimit: float
    symbol: str
    comment: str
    external_id: str


class MockPosition(NamedTuple):
    """Mock position structure."""

    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str


class MockDeal(NamedTuple):
    """Mock deal structure."""

    ticket: int
    order: int
    time: int
    time_msc: int
    type: int
    entry: int
    magic: int
    position_id: int
    reason: int
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    symbol: str
    comment: str
    external_id: str


class MockOrderCheckResult(NamedTuple):
    """Mock order check result structure."""

    retcode: int
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    comment: str
    request_id: int


class MockOrderSendResult(NamedTuple):
    """Mock order send result structure."""

    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str
    request_id: int


class MockBookInfo(NamedTuple):
    """Mock book info structure."""

    type: int
    price: float
    volume: float
    volume_real: float


class TestMt5Config:
    """Test Mt5Config class."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = Mt5Config()  # pyright: ignore[reportCallIssue]
        assert config.path is None
        assert config.login is None
        assert config.password is None
        assert config.server is None
        assert config.timeout is None

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = Mt5Config(
            login=123456,
            password="secret",
            server="Demo-Server",
            timeout=30000,
        )
        assert config.login == 123456
        assert config.password == "secret"  # noqa: S105
        assert config.server == "Demo-Server"
        assert config.timeout == 30000

    def test_config_immutable(self) -> None:
        """Test that config is immutable."""
        config = Mt5Config()  # pyright: ignore[reportCallIssue]
        with pytest.raises(ValidationError):
            config.login = 123456


class TestMt5DataClient:
    """Test Mt5DataClient class."""

    def test_init_default(self, mock_mt5_import: ModuleType | None) -> None:
        """Test client initialization with default config."""
        assert mock_mt5_import is not None
        client = Mt5DataClient(mt5=mock_mt5_import)
        assert client.config is not None
        assert client.config.timeout is None
        assert not client._is_initialized

    def test_init_custom_config(self, mock_mt5_import: ModuleType | None) -> None:
        """Test client initialization with custom config."""
        assert mock_mt5_import is not None
        config = Mt5Config(
            login=123456,
            password="test",
            server="test-server",
            timeout=30000,
        )
        client = Mt5DataClient(mt5=mock_mt5_import, config=config)
        assert client.config == config
        assert client.config.login == 123456
        assert client.config.timeout == 30000

    def test_mt5_module_default_factory(self, mocker: MockerFixture) -> None:
        """Test initialization with default mt5 module factory."""
        # Mock the importlib.import_module to verify it's called
        mock_import = mocker.patch("importlib.import_module")
        mock_import.return_value = mocker.MagicMock()

        client = Mt5DataClient()  # pyright: ignore[reportCallIssue]

        # Verify that importlib.import_module was called with "MetaTrader5"
        mock_import.assert_called_once_with("MetaTrader5")
        assert client.mt5 == mock_import.return_value

    def test_initialize_success(self, mock_mt5_import: ModuleType | None) -> None:
        """Test successful initialization."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        result = client.initialize()

        assert result is True
        assert client._is_initialized is True
        mock_mt5_import.initialize.assert_called_once()

    def test_initialize_failure(self, mock_mt5_import: ModuleType | None) -> None:
        """Test initialization failure."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = False
        mock_mt5_import.last_error.return_value = (1, "Connection failed")

        client = Mt5DataClient(mt5=mock_mt5_import, retry_count=0)
        pattern = (
            r"MT5 initialize and login failed after 0 retries: "
            r"\(1, 'Connection failed'\)"
        )
        with pytest.raises(Mt5RuntimeError, match=pattern):
            client.initialize_and_login_mt5()

    def test_initialize_already_initialized(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test initialize when already initialized."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        # Set _is_initialized to True to test the early return path
        client._is_initialized = True

        # Call initialize when already initialized - should still call mt5.initialize
        result = client.initialize()

        assert result is True  # Method returns True when successful
        mock_mt5_import.initialize.assert_called_once()

    def test_shutdown(self, mock_mt5_import: ModuleType | None) -> None:
        """Test shutdown."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        client.shutdown()

        assert client._is_initialized is False
        mock_mt5_import.shutdown.assert_called_once()

    def test_context_manager(self, mock_mt5_import: ModuleType | None) -> None:
        """Test context manager functionality."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        with Mt5DataClient(mt5=mock_mt5_import) as client:
            assert client._is_initialized is True
            mock_mt5_import.initialize.assert_called_once()

        mock_mt5_import.shutdown.assert_called_once()

    @pytest.mark.parametrize(
        ("client_method", "mt5_method"),
        [
            ("orders_get_as_df", "orders_get"),
            ("positions_get_as_df", "positions_get"),
        ],
    )
    def test_orders_positions_get_empty(
        self, mock_mt5_import: ModuleType | None, client_method: str, mt5_method: str
    ) -> None:
        """Test orders_get/positions_get methods with empty result."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        getattr(mock_mt5_import, mt5_method).return_value = []

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        df_result = getattr(client, client_method)()
        assert df_result.empty
        assert isinstance(df_result, pd.DataFrame)

    def test_error_handling_without_mt5(self) -> None:
        """Test error handling when an invalid mt5 module is provided."""
        # Test with an invalid mt5 module object
        invalid_mt5 = object()  # Not a proper module
        with pytest.raises(ValidationError):
            Mt5DataClient(mt5=invalid_mt5)  # type: ignore[arg-type]

    def test_ensure_initialized_calls_initialize(
        self,
        mock_mt5_import: ModuleType | None,
    ) -> None:
        """Test that _ensure_initialized calls initialize if not initialized."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.account_info.return_value = MockAccountInfo(
            login=123456,
            trade_mode=0,
            leverage=100,
            limit_orders=200,
            margin_so_mode=0,
            trade_allowed=True,
            trade_expert=True,
            margin_mode=0,
            currency_digits=2,
            fifo_close=False,
            balance=10000.0,
            credit=0.0,
            profit=100.0,
            equity=10100.0,
            margin=500.0,
            margin_free=9600.0,
            margin_level=2020.0,
            margin_so_call=50.0,
            margin_so_so=25.0,
            margin_initial=0.0,
            margin_maintenance=0.0,
            assets=0.0,
            liabilities=0.0,
            commission_blocked=0.0,
            name="Demo Account",
            server="Demo-Server",
            currency="USD",
            company="Test Company",
        )

        client = Mt5DataClient(mt5=mock_mt5_import)
        # Initialize the client first
        client.initialize()
        df_result = client.account_info_as_df()

        assert client._is_initialized is True
        mock_mt5_import.initialize.assert_called_once()
        assert isinstance(df_result, pd.DataFrame)

    def test_terminal_info_as_df(self, mock_mt5_import: ModuleType | None) -> None:
        """Test terminal_info_as_df method."""
        assert mock_mt5_import is not None

        class MockTerminalInfo:
            def _asdict(self) -> dict[str, Any]:
                return {"name": "MetaTrader 5", "version": 123}

        mock_mt5_import.terminal_info.return_value = MockTerminalInfo()

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        df_result = client.terminal_info_as_df()

        mock_mt5_import.initialize.assert_called_once()
        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert "name" in df_result.columns
        assert "version" in df_result.columns

    def test_orders_get_with_data(self, mock_mt5_import: ModuleType | None) -> None:
        """Test orders_get method with data."""
        assert mock_mt5_import is not None
        mock_orders = [
            MockOrder(
                ticket=123456,
                time_setup=1640995200,
                time_setup_msc=1640995200000,
                time_done=0,
                time_done_msc=0,
                time_expiration=0,
                type=0,
                type_time=0,
                type_filling=0,
                state=1,
                magic=0,
                position_id=0,
                position_by_id=0,
                reason=0,
                volume_initial=0.1,
                volume_current=0.1,
                price_open=1.1300,
                sl=1.1200,
                tp=1.1400,
                price_current=1.1301,
                price_stoplimit=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.orders_get.return_value = mock_orders

        client.initialize()
        df_result = client.orders_get_as_df(symbol="EURUSD", index_keys="ticket")

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.index[0] == 123456
        assert df_result.iloc[0]["symbol"] == "EURUSD"
        assert df_result.iloc[0]["volume_initial"] == 0.1
        assert df_result.iloc[0]["time_setup"] == pd.to_datetime(1640995200, unit="s")
        assert df_result.iloc[0]["time_setup_msc"] == pd.to_datetime(
            1640995200000, unit="ms"
        )

    def test_positions_get_with_data(self, mock_mt5_import: ModuleType | None) -> None:
        """Test positions_get method with data."""
        assert mock_mt5_import is not None
        mock_positions = [
            MockPosition(
                ticket=123456,
                time=1640995200,
                time_msc=1640995200000,
                time_update=1640995200,
                time_update_msc=1640995200000,
                type=0,
                magic=0,
                identifier=123456,
                reason=0,
                volume=0.1,
                price_open=1.1300,
                sl=1.1200,
                tp=1.1400,
                price_current=1.1301,
                swap=-0.5,
                profit=1.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.positions_get.return_value = mock_positions

        client.initialize()
        df_result = client.positions_get_as_df(symbol="EURUSD", index_keys="ticket")

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.index[0] == 123456
        assert df_result.iloc[0]["symbol"] == "EURUSD"
        assert df_result.iloc[0]["volume"] == 0.1
        # Time fields should be present (conversion behavior may vary)
        assert "time" in df_result.columns
        assert "time_msc" in df_result.columns

    @pytest.mark.parametrize(
        ("timeout", "expected_kwargs"),
        [
            (None, {"password": "password", "server": "server.com"}),
            (30000, {"password": "password", "server": "server.com", "timeout": 30000}),
        ],
    )
    def test_login_success(
        self,
        mock_mt5_import: ModuleType | None,
        timeout: int | None,
        expected_kwargs: dict[str, Any],
    ) -> None:
        """Test login method success with and without timeout."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.login.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.login(123456, "password", "server.com", timeout=timeout)

        assert result is True
        mock_mt5_import.login.assert_called_once_with(123456, **expected_kwargs)

    def test_login_failure(self, mock_mt5_import: ModuleType | None) -> None:
        """Test login method failure."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.login.return_value = False

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.login(123456, "password", "server.com")

        assert result is False

    @pytest.mark.parametrize(
        ("client_method", "mt5_method", "return_value"),
        [
            ("orders_total", "orders_total", 5),
            ("orders_total", "orders_total", None),
            ("positions_total", "positions_total", 3),
            ("positions_total", "positions_total", None),
            ("symbols_total", "symbols_total", 1000),
            ("symbols_total", "symbols_total", None),
        ],
    )
    def test_total_methods(
        self,
        mock_mt5_import: ModuleType | None,
        client_method: str,
        mt5_method: str,
        return_value: int | None,
    ) -> None:
        """Test total-returning methods with values and None."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        getattr(mock_mt5_import, mt5_method).return_value = return_value

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = getattr(client, client_method)()

        assert result == return_value

    @pytest.mark.parametrize(
        ("client_method", "mt5_method", "return_value"),
        [
            ("history_orders_total", "history_orders_total", 10),
            ("history_orders_total", "history_orders_total", 0),
            ("history_orders_total", "history_orders_total", None),
            ("history_deals_total", "history_deals_total", 15),
            ("history_deals_total", "history_deals_total", 0),
            ("history_deals_total", "history_deals_total", None),
        ],
    )
    def test_history_totals_methods(
        self,
        mock_mt5_import: ModuleType | None,
        client_method: str,
        mt5_method: str,
        return_value: int | None,
    ) -> None:
        """Test history total methods with varied return values."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        getattr(mock_mt5_import, mt5_method).return_value = return_value

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = getattr(client, client_method)(
            datetime(2022, 1, 1, tzinfo=UTC),
            datetime(2022, 1, 2, tzinfo=UTC),
        )

        assert result == return_value

    @pytest.mark.parametrize(
        ("volume", "price", "last_error"),
        [
            (0.1, 1.1300, None),
            (0.0, 1.1300, "Invalid volume"),
            (0.1, 0.0, "Invalid price"),
            (0.1, 1.1300, "Order calc margin failed"),
        ],
    )
    def test_order_calc_margin(
        self,
        mock_mt5_import: ModuleType | None,
        volume: float,
        price: float,
        last_error: str | None,
    ) -> None:
        """Test order_calc_margin with success and failure paths."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.order_calc_margin.return_value = (
            100.0 if last_error is None else None
        )
        if last_error is not None:
            mock_mt5_import.last_error.return_value = (1, last_error)

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        if last_error is None:
            result = client.order_calc_margin(0, "EURUSD", volume, price)
            assert result == 100.0
        else:
            with pytest.raises(
                Mt5RuntimeError, match=r"MT5 order_calc_margin returned None"
            ):
                client.order_calc_margin(0, "EURUSD", volume, price)

    def test_order_calc_profit(self, mock_mt5_import: ModuleType | None) -> None:
        """Test order_calc_profit method."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.order_calc_profit.return_value = 10.0

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.order_calc_profit(0, "EURUSD", 0.1, 1.1300, 1.1400)

        assert result == 10.0

    def test_order_calc_profit_invalid_volume(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test order_calc_profit method with invalid volume."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.order_calc_profit.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Invalid volume")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            Mt5RuntimeError, match=r"MT5 order_calc_profit returned None"
        ):
            client.order_calc_profit(0, "EURUSD", 0.0, 1.1300, 1.1400)

    def test_order_calc_profit_invalid_price_open(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test order_calc_profit method with invalid open price."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.order_calc_profit.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Invalid price_open")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            Mt5RuntimeError, match=r"MT5 order_calc_profit returned None"
        ):
            client.order_calc_profit(0, "EURUSD", 0.1, 0.0, 1.1400)

    def test_order_calc_profit_invalid_price_close(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test order_calc_profit method with invalid close price."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.order_calc_profit.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Invalid price_close")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            Mt5RuntimeError, match=r"MT5 order_calc_profit returned None"
        ):
            client.order_calc_profit(0, "EURUSD", 0.1, 1.1300, 0.0)

    def test_order_calc_profit_error(self, mock_mt5_import: ModuleType | None) -> None:
        """Test order_calc_profit method with error."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.order_calc_profit.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Order calc profit failed")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            Mt5RuntimeError,
            match=r"MT5 order_calc_profit returned None",
        ):
            client.order_calc_profit(0, "EURUSD", 0.1, 1.1300, 1.1400)

    def test_version(self, mock_mt5_import: ModuleType | None) -> None:
        """Test version method."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.version.return_value = (2460, 2460, "15 Feb 2022")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.version()

        assert result == (2460, 2460, "15 Feb 2022")

    def test_version_none_result(self, mock_mt5_import: ModuleType | None) -> None:
        """Test version method with None result."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.version.return_value = None

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.version()

        assert result is None

    def test_symbols_total(self, mock_mt5_import: ModuleType | None) -> None:
        """Test symbols_total method."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbols_total.return_value = 1000

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.symbols_total()

        assert result == 1000

    def test_symbols_total_none_result(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test symbols_total method with None result."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbols_total.return_value = None

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.symbols_total()

        assert result is None

    def test_symbol_select(self, mock_mt5_import: ModuleType | None) -> None:
        """Test symbol_select method."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbol_select.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.symbol_select("EURUSD")

        assert result is True

    def test_symbol_select_disable(self, mock_mt5_import: ModuleType | None) -> None:
        """Test symbol_select method with disable."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbol_select.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.symbol_select("EURUSD", enable=False)

        assert result is True

    def test_symbol_select_error(self, mock_mt5_import: ModuleType | None) -> None:
        """Test symbol_select method with error."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbol_select.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Symbol select failed")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(Mt5RuntimeError, match=r"MT5 symbol_select returned None"):
            client.symbol_select("EURUSD")

    def test_market_book_add(self, mock_mt5_import: ModuleType | None) -> None:
        """Test market_book_add method."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.market_book_add.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.market_book_add("EURUSD")

        assert result is True

    def test_market_book_add_error(self, mock_mt5_import: ModuleType | None) -> None:
        """Test market_book_add method with error."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.market_book_add.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Market book add failed")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(Mt5RuntimeError, match=r"MT5 market_book_add returned None"):
            client.market_book_add("EURUSD")

    def test_market_book_release(self, mock_mt5_import: ModuleType | None) -> None:
        """Test market_book_release method."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.market_book_release.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        result = client.market_book_release("EURUSD")

        assert result is True

    def test_market_book_release_error(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test market_book_release method with error."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.market_book_release.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Market book release failed")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            Mt5RuntimeError,
            match=r"MT5 market_book_release returned None",
        ):
            client.market_book_release("EURUSD")

    def test_history_orders_get_ticket(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get method with ticket filter."""
        assert mock_mt5_import is not None
        mock_orders = [
            MockOrder(
                ticket=123456,
                time_setup=1640995200,
                time_setup_msc=1640995200000,
                time_done=0,
                time_done_msc=0,
                time_expiration=0,
                type=0,
                type_time=0,
                type_filling=0,
                state=1,
                magic=0,
                position_id=0,
                position_by_id=0,
                reason=0,
                volume_initial=0.1,
                volume_current=0.1,
                price_open=1.1300,
                sl=1.1200,
                tp=1.1400,
                price_current=1.1301,
                price_stoplimit=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = mock_orders

        client.initialize()
        df_result = client.history_orders_get_as_df(ticket=123456, index_keys="ticket")

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.index[0] == 123456

    def test_history_orders_get_position(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get method with position filter."""
        assert mock_mt5_import is not None
        mock_orders = [
            MockOrder(
                ticket=123456,
                time_setup=1640995200,
                time_setup_msc=1640995200000,
                time_done=0,
                time_done_msc=0,
                time_expiration=0,
                type=0,
                type_time=0,
                type_filling=0,
                state=1,
                magic=0,
                position_id=345678,
                position_by_id=0,
                reason=0,
                volume_initial=0.1,
                volume_current=0.1,
                price_open=1.1300,
                sl=1.1200,
                tp=1.1400,
                price_current=1.1301,
                price_stoplimit=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = mock_orders

        client.initialize()
        df_result = client.history_orders_get_as_df(position=345678)

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.iloc[0]["position_id"] == 345678

    def test_history_orders_get_no_dates(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get method without dates when not using ticket."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = []
        mock_mt5_import.last_error.return_value = (1, "Invalid arguments")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            ValueError,
            match=(
                r"Both date_from and date_to must be provided"
                r" if not using ticket or position"
            ),
        ):
            client.history_orders_get_as_df()

    def test_history_orders_get_invalid_dates(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get method with invalid date range."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(ValueError, match=r"Invalid date range"):
            client.history_orders_get_as_df(
                datetime(2022, 1, 2, tzinfo=UTC),
                datetime(2022, 1, 1, tzinfo=UTC),
            )

    def test_history_orders_get_with_symbol(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get method with symbol filter."""
        assert mock_mt5_import is not None
        mock_orders = [
            MockOrder(
                ticket=123456,
                time_setup=1640995200,
                time_setup_msc=1640995200000,
                time_done=0,
                time_done_msc=0,
                time_expiration=0,
                type=0,
                type_time=0,
                type_filling=0,
                state=1,
                magic=0,
                position_id=0,
                position_by_id=0,
                reason=0,
                volume_initial=0.1,
                volume_current=0.1,
                price_open=1.1300,
                sl=1.1200,
                tp=1.1400,
                price_current=1.1301,
                price_stoplimit=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = mock_orders

        client.initialize()
        df_result = client.history_orders_get_as_df(
            datetime(2022, 1, 1, tzinfo=UTC),
            datetime(2022, 1, 2, tzinfo=UTC),
            symbol="EURUSD",
        )

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.iloc[0]["symbol"] == "EURUSD"

    def test_history_orders_get_with_group(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get method with group filter."""
        assert mock_mt5_import is not None
        mock_orders = [
            MockOrder(
                ticket=123456,
                time_setup=1640995200,
                time_setup_msc=1640995200000,
                time_done=0,
                time_done_msc=0,
                time_expiration=0,
                type=0,
                type_time=0,
                type_filling=0,
                state=1,
                magic=0,
                position_id=0,
                position_by_id=0,
                reason=0,
                volume_initial=0.1,
                volume_current=0.1,
                price_open=1.1300,
                sl=1.1200,
                tp=1.1400,
                price_current=1.1301,
                price_stoplimit=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = mock_orders

        client.initialize()
        df_result = client.history_orders_get_as_df(
            datetime(2022, 1, 1, tzinfo=UTC),
            datetime(2022, 1, 2, tzinfo=UTC),
            group="*USD*",
        )

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.iloc[0]["symbol"] == "EURUSD"

    def test_history_orders_get_empty(self, mock_mt5_import: ModuleType | None) -> None:
        """Test history_orders_get method with empty result."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = []

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        orders_df = client.history_orders_get_as_df(
            datetime(2022, 1, 1, tzinfo=UTC),
            datetime(2022, 1, 2, tzinfo=UTC),
        )
        assert orders_df.empty
        assert isinstance(orders_df, pd.DataFrame)

    def test_history_deals_get_no_dates(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_deals_get method without dates when not using ticket."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_deals_get.return_value = []
        mock_mt5_import.last_error.return_value = (1, "Invalid arguments")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(
            ValueError,
            match=(
                r"Both date_from and date_to must be provided"
                r" if not using ticket or position"
            ),
        ):
            client.history_deals_get_as_df()

    def test_market_book_get(self, mock_mt5_import: ModuleType | None) -> None:
        """Test market_book_get method."""
        assert mock_mt5_import is not None
        mock_book = [
            MockBookInfo(
                type=0,
                price=1.1300,
                volume=100.0,
                volume_real=100.0,
            ),
            MockBookInfo(
                type=1,
                price=1.1302,
                volume=200.0,
                volume_real=200.0,
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.market_book_get.return_value = tuple(mock_book)

        client.initialize()
        result = client.market_book_get("EURUSD")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0].type == 0
        assert result[0].price == 1.1300
        assert result[1].type == 1
        assert result[1].price == 1.1302

    def test_market_book_get_error(self, mock_mt5_import: ModuleType | None) -> None:
        """Test market_book_get method with error."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.market_book_get.return_value = None
        mock_mt5_import.last_error.return_value = (1, "Market book get failed")

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        with pytest.raises(Mt5RuntimeError, match=r"MT5 market_book_get returned None"):
            client.market_book_get("EURUSD")

    def test_shutdown_when_not_initialized(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test shutdown method when already not initialized."""
        assert mock_mt5_import is not None

        client = Mt5DataClient(mt5=mock_mt5_import)
        # Don't initialize
        client.shutdown()  # Should call mt5.shutdown()

        mock_mt5_import.shutdown.assert_called_once()

    def test_orders_get_missing_time_columns(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test orders_get when some time columns are missing."""
        assert mock_mt5_import is not None
        # Create mock orders data as dict without time_expiration

        class MockOrderNoTimeExpiration:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "ticket": 123456,
                    "time_setup": 1640995200,
                    "time_setup_msc": 1640995200000,
                    "time_done": 0,
                    "time_done_msc": 0,
                    "type": 0,
                    "type_time": 0,
                    "type_filling": 0,
                    "state": 1,
                    "magic": 0,
                    "position_id": 0,
                    "position_by_id": 0,
                    "reason": 0,
                    "volume_initial": 0.1,
                    "volume_current": 0.1,
                    "price_open": 1.1300,
                    "sl": 1.1200,
                    "tp": 1.1400,
                    "price_current": 1.1301,
                    "price_stoplimit": 0.0,
                    "symbol": "EURUSD",
                    "comment": "",
                    "external_id": "",
                }

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.orders_get.return_value = [MockOrderNoTimeExpiration()]

        client.initialize()
        df_result = client.orders_get_as_df()

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert "time_expiration" not in df_result.columns

    def test_positions_get_missing_time_columns(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test positions_get when some time columns are missing."""
        assert mock_mt5_import is not None
        # Create mock positions data as dict without time_update

        class MockPositionNoTimeUpdate:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "ticket": 123456,
                    "time": 1640995200,
                    "time_msc": 1640995200000,
                    "time_update_msc": 1640995200000,
                    "type": 0,
                    "magic": 0,
                    "identifier": 123456,
                    "reason": 0,
                    "volume": 0.1,
                    "price_open": 1.1300,
                    "sl": 1.1200,
                    "tp": 1.1400,
                    "price_current": 1.1301,
                    "swap": 0.0,
                    "profit": 10.0,
                    "symbol": "EURUSD",
                    "comment": "",
                    "external_id": "",
                }

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.positions_get.return_value = [MockPositionNoTimeUpdate()]

        client.initialize()
        df_result = client.positions_get_as_df()

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert "time_update" not in df_result.columns

    def test_history_orders_get_missing_time_columns(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_orders_get when some time columns are missing."""
        assert mock_mt5_import is not None
        # Create mock orders data as dict without time_done

        class MockOrderNoTimeDone:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "ticket": 123456,
                    "time_setup": 1640995200,
                    "time_setup_msc": 1640995200000,
                    "time_done_msc": 0,
                    "time_expiration": 0,
                    "type": 0,
                    "type_time": 0,
                    "type_filling": 0,
                    "state": 1,
                    "magic": 0,
                    "position_id": 0,
                    "position_by_id": 0,
                    "reason": 0,
                    "volume_initial": 0.1,
                    "volume_current": 0.1,
                    "price_open": 1.1300,
                    "sl": 1.1200,
                    "tp": 1.1400,
                    "price_current": 1.1301,
                    "price_stoplimit": 0.0,
                    "symbol": "EURUSD",
                    "comment": "",
                    "external_id": "",
                }

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_orders_get.return_value = [MockOrderNoTimeDone()]

        client.initialize()
        df_result = client.history_orders_get_as_df(
            datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 2, tzinfo=UTC)
        )

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert "time_done" not in df_result.columns


class TestMt5DataClientValidation:
    """Test Mt5DataClient validation methods."""

    def test_validate_positive_count_valid(self) -> None:
        """Test _validate_positive_count with valid count."""
        # Should not raise for positive count
        Mt5DataClient._validate_positive_count(count=1)
        Mt5DataClient._validate_positive_count(count=100)

    def test_validate_positive_count_invalid(self) -> None:
        """Test _validate_positive_count with invalid count."""
        with pytest.raises(
            ValueError, match=r"Invalid count: 0\. Count must be positive\."
        ):
            Mt5DataClient._validate_positive_count(count=0)

        with pytest.raises(
            ValueError, match=r"Invalid count: -1\. Count must be positive\."
        ):
            Mt5DataClient._validate_positive_count(count=-1)

    def test_validate_date_range_valid(self) -> None:
        """Test _validate_date_range with valid date range."""
        date_from = datetime(2023, 1, 1, tzinfo=UTC)
        date_to = datetime(2023, 1, 2, tzinfo=UTC)
        # Should not raise for valid date range
        Mt5DataClient._validate_date_range(date_from=date_from, date_to=date_to)

    def test_validate_date_range_invalid(self) -> None:
        """Test _validate_date_range with invalid date range."""
        date_from = datetime(2023, 1, 2, tzinfo=UTC)
        date_to = datetime(2023, 1, 1, tzinfo=UTC)
        with pytest.raises(
            ValueError, match=r"Invalid date range: from=.* must be before to=.*"
        ):
            Mt5DataClient._validate_date_range(date_from=date_from, date_to=date_to)

    def test_validate_positive_value_valid(self) -> None:
        """Test _validate_positive_value with valid values."""
        # Should not raise for positive values
        Mt5DataClient._validate_positive_value(value=1.0, name="volume")
        Mt5DataClient._validate_positive_value(value=0.1, name="volume")

    def test_validate_positive_value_invalid(self) -> None:
        """Test _validate_positive_value with invalid volume."""
        with pytest.raises(
            ValueError, match=r"Invalid volume: 0\. Volume must be positive\."
        ):
            Mt5DataClient._validate_positive_value(value=0, name="volume")

        with pytest.raises(
            ValueError, match=r"Invalid volume: -1\. Volume must be positive\."
        ):
            Mt5DataClient._validate_positive_value(value=-1, name="volume")

    def test_validate_positive_value_price_invalid(self) -> None:
        """Test _validate_positive_value with invalid price."""
        with pytest.raises(
            ValueError, match=r"Invalid price_open: 0\. Price must be positive\."
        ):
            Mt5DataClient._validate_positive_value(value=0, name="price_open")

        with pytest.raises(
            ValueError, match=r"Invalid price_close: -1\. Price must be positive\."
        ):
            Mt5DataClient._validate_positive_value(value=-1, name="price_close")

    def test_validate_non_negative_position_valid(self) -> None:
        """Test _validate_non_negative_position with valid position."""
        # Should not raise for non-negative position
        Mt5DataClient._validate_non_negative_position(position=0)
        Mt5DataClient._validate_non_negative_position(position=10)

    def test_validate_non_negative_position_invalid(self) -> None:
        """Test _validate_non_negative_position with invalid position."""
        with pytest.raises(
            ValueError,
            match=r"Invalid start_pos: -1\. Position must be non-negative\.",
        ):
            Mt5DataClient._validate_non_negative_position(position=-1)

    def test_order_check_as_dict(
        self,
        mock_mt5_import: ModuleType,
        mocker: MockerFixture,
    ) -> None:
        """Test order_check_as_dict method."""
        config = Mt5Config()

        # Mock order check result with nested structure
        mock_request = mocker.MagicMock()
        mock_request._asdict.return_value = {"action": 1, "symbol": "EURUSD"}

        mock_result = mocker.MagicMock()
        mock_result._asdict.return_value = {
            "retcode": 10009,
            "request": mock_request,
            "volume": 1.0,
        }

        with Mt5DataClient(mt5=mock_mt5_import, config=config) as client:
            mock_mt5_import.order_check.return_value = mock_result

            result = client.order_check_as_dict(
                request={"action": 1, "symbol": "EURUSD"}
            )

            assert result["retcode"] == 10009
            assert result["request"] == {"action": 1, "symbol": "EURUSD"}
            assert result["volume"] == 1.0

    def test_order_send_as_dict(
        self,
        mock_mt5_import: ModuleType,
        mocker: MockerFixture,
    ) -> None:
        """Test order_send_as_dict method."""
        config = Mt5Config()

        # Mock order send result with nested structure
        mock_request = mocker.MagicMock()
        mock_request._asdict.return_value = {"action": 1, "symbol": "EURUSD"}

        mock_result = mocker.MagicMock()
        mock_result._asdict.return_value = {
            "retcode": 10009,
            "request": mock_request,
            "order": 12345,
        }

        with Mt5DataClient(mt5=mock_mt5_import, config=config) as client:
            mock_mt5_import.order_send.return_value = mock_result

            result = client.order_send_as_dict(
                request={"action": 1, "symbol": "EURUSD"}
            )

            assert result["retcode"] == 10009
            assert result["request"] == {"action": 1, "symbol": "EURUSD"}
            assert result["order"] == 12345

    def test_copy_rates_from_as_df(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test copy_rates_from_as_df method to cover validation line."""
        config = Mt5Config()

        # Mock rates data
        rate_dtype = np.dtype([
            ("time", "int64"),
            ("open", "float64"),
            ("high", "float64"),
            ("low", "float64"),
            ("close", "float64"),
        ])
        mock_rates = np.array(
            [
                (1640995200, 1.1300, 1.1350, 1.1280, 1.1320),
            ],
            dtype=rate_dtype,
        )

        with Mt5DataClient(mt5=mock_mt5_import, config=config) as client:
            mock_mt5_import.copy_rates_from.return_value = mock_rates

            # This should trigger the _validate_positive_count call
            result = client.copy_rates_from_as_df(
                symbol="EURUSD",
                timeframe=16385,
                date_from=datetime(2023, 1, 1, tzinfo=UTC),
                count=10,
                index_keys="time",
            )

            assert len(result) == 1
            assert "time" in result.index.names

    def test_copy_rates_range_as_df(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test copy_rates_range_as_df method to cover validation line."""
        config = Mt5Config()

        # Mock rates data
        rate_dtype = np.dtype([
            ("time", "int64"),
            ("open", "float64"),
            ("high", "float64"),
            ("low", "float64"),
            ("close", "float64"),
        ])
        mock_rates = np.array(
            [
                (1640995200, 1.1300, 1.1350, 1.1280, 1.1320),
            ],
            dtype=rate_dtype,
        )

        with Mt5DataClient(mt5=mock_mt5_import, config=config) as client:
            mock_mt5_import.copy_rates_range.return_value = mock_rates

            # This should trigger the _validate_date_range call
            result = client.copy_rates_range_as_df(
                symbol="EURUSD",
                timeframe=16385,
                date_from=datetime(2023, 1, 1, tzinfo=UTC),
                date_to=datetime(2023, 1, 2, tzinfo=UTC),
                index_keys="time",
            )

            assert len(result) == 1
            assert "time" in result.index.names


class TestMt5DataClientRetryLogic:
    """Tests for Mt5DataClient retry logic and additional coverage."""

    def test_initialize_with_retry_logic(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test initialize method with retry logic."""
        assert mock_mt5_import is not None

        client = Mt5DataClient(mt5=mock_mt5_import, retry_count=2)

        # Mock initialize to fail first two times, succeed on third
        mock_mt5_import.initialize.side_effect = [False, False, True]
        mock_mt5_import.last_error.return_value = (1, "Test error")

        # Should succeed on third attempt
        client.initialize_and_login_mt5()

        assert mock_mt5_import.initialize.call_count == 3

    def test_initialize_with_retry_logic_warning_path(
        self, mock_mt5_import: ModuleType | None, mocker: MockerFixture
    ) -> None:
        """Test initialize method with retry logic warning path."""
        assert mock_mt5_import is not None

        client = Mt5DataClient(mt5=mock_mt5_import, retry_count=1)

        # Mock initialize to fail first time, succeed on second
        mock_mt5_import.initialize.side_effect = [False, True]
        mock_mt5_import.last_error.return_value = (1, "Test error")

        # Mock time.sleep to capture the call
        mock_sleep = mocker.patch("pdmt5.dataframe.time.sleep")

        # Should succeed on second attempt
        client.initialize_and_login_mt5()

        assert mock_mt5_import.initialize.call_count == 2
        mock_sleep.assert_called_once_with(1)

    def test_initialize_with_retry_all_failures(
        self, mock_mt5_import: ModuleType | None, mocker: MockerFixture
    ) -> None:
        """Test initialize method with retry logic when all attempts fail."""
        assert mock_mt5_import is not None

        client = Mt5DataClient(mt5=mock_mt5_import, retry_count=2)

        # Mock initialize to fail all times
        mock_mt5_import.initialize.return_value = False
        mock_mt5_import.last_error.return_value = (1, "Test error")

        # Mock time.sleep to capture the calls
        mock_sleep = mocker.patch("pdmt5.dataframe.time.sleep")

        with pytest.raises(Mt5RuntimeError) as exc_info:
            client.initialize_and_login_mt5()

        assert "MT5 initialize and login failed after" in str(exc_info.value)
        assert mock_mt5_import.initialize.call_count == 3  # All attempts made
        # Check that sleep was called for retries
        assert mock_sleep.call_count == 2

    def test_account_info_as_dict(self, mock_mt5_import: ModuleType | None) -> None:
        """Test account_info_as_dict method."""
        assert mock_mt5_import is not None
        mock_account = MockAccountInfo(
            login=123456,
            trade_mode=0,
            leverage=100,
            limit_orders=200,
            margin_so_mode=0,
            trade_allowed=True,
            trade_expert=True,
            margin_mode=0,
            currency_digits=2,
            fifo_close=False,
            balance=10000.0,
            credit=0.0,
            profit=100.0,
            equity=10100.0,
            margin=500.0,
            margin_free=9600.0,
            margin_level=2020.0,
            margin_so_call=50.0,
            margin_so_so=25.0,
            margin_initial=0.0,
            margin_maintenance=0.0,
            assets=0.0,
            liabilities=0.0,
            commission_blocked=0.0,
            name="Demo Account",
            server="Demo-Server",
            currency="USD",
            company="Test Company",
        )

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.account_info.return_value = mock_account

        client.initialize()
        dict_result = client.account_info_as_dict()

        assert isinstance(dict_result, dict)
        assert dict_result["login"] == 123456
        assert dict_result["balance"] == 10000.0
        assert dict_result["currency"] == "USD"
        assert dict_result["server"] == "Demo-Server"
        assert dict_result["trade_allowed"] is True

    def test_terminal_info_as_dict(self, mock_mt5_import: ModuleType | None) -> None:
        """Test terminal_info_as_dict method."""
        assert mock_mt5_import is not None
        mock_terminal = MockTerminalInfo(
            community_account=True,
            community_connection=True,
            connected=True,
            dlls_allowed=False,
            trade_allowed=True,
            tradeapi_disabled=False,
            email_enabled=True,
            ftp_enabled=False,
            notifications_enabled=True,
            mqid=True,
            build=3815,
            maxbars=65000,
            codepage=1252,
            ping_last=50,
            community_balance=1000,
            retransmission=0.0,
            company="Test Broker",
            name="MetaTrader 5",
            language=1033,
            path="C:\\Program Files\\MetaTrader 5",
            data_path="C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\123",
            commondata_path="C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common",
        )

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.terminal_info.return_value = mock_terminal

        client.initialize()
        dict_result = client.terminal_info_as_dict()

        assert isinstance(dict_result, dict)
        assert dict_result["connected"] is True
        assert dict_result["trade_allowed"] is True
        assert dict_result["build"] == 3815
        assert dict_result["company"] == "Test Broker"
        assert dict_result["name"] == "MetaTrader 5"

    def test_symbol_info_as_dict(self, mock_mt5_import: ModuleType | None) -> None:
        """Test symbol_info_as_dict method."""
        assert mock_mt5_import is not None
        mock_symbol = MockSymbolInfo(
            custom=False,
            chart_mode=0,
            select=True,
            visible=True,
            session_deals=0,
            session_buy_orders=0,
            session_sell_orders=0,
            volume=0,
            volumehigh=0,
            volumelow=0,
            time=1640995200,
            digits=5,
            spread=10,
            spread_float=True,
            ticks_bookdepth=10,
            trade_calc_mode=0,
            trade_mode=4,
            start_time=0,
            expiration_time=0,
            trade_stops_level=0,
            trade_freeze_level=0,
            trade_exemode=1,
            swap_mode=1,
            swap_rollover3days=3,
            margin_hedged_use_leg=False,
            expiration_mode=7,
            filling_mode=1,
            order_mode=127,
            order_gtc_mode=0,
            option_mode=0,
            option_right=0,
            bid=1.13200,
            bidhigh=1.13500,
            bidlow=1.13000,
            ask=1.13210,
            askhigh=1.13510,
            asklow=1.13010,
            last=1.13205,
            lasthigh=1.13505,
            lastlow=1.13005,
            volume_real=1000000.0,
            volumehigh_real=2000000.0,
            volumelow_real=500000.0,
            option_strike=0.0,
            point=0.00001,
            trade_tick_value=1.0,
            trade_tick_value_profit=1.0,
            trade_tick_value_loss=1.0,
            trade_tick_size=0.00001,
            trade_contract_size=100000.0,
            trade_accrued_interest=0.0,
            trade_face_value=0.0,
            trade_liquidity_rate=0.0,
            volume_min=0.01,
            volume_max=500.0,
            volume_step=0.01,
            volume_limit=0.0,
            swap_long=-0.5,
            swap_short=-0.3,
            margin_initial=0.0,
            margin_maintenance=0.0,
            session_volume=0.0,
            session_turnover=0.0,
            session_interest=0.0,
            session_buy_orders_volume=0.0,
            session_sell_orders_volume=0.0,
            session_open=1.13100,
            session_close=1.13200,
            session_aw=0.0,
            session_price_settlement=0.0,
            session_price_limit_min=0.0,
            session_price_limit_max=0.0,
            margin_hedged=50000.0,
            price_change=0.0010,
            price_volatility=0.0,
            price_theoretical=0.0,
            price_greeks_delta=0.0,
            price_greeks_theta=0.0,
            price_greeks_gamma=0.0,
            price_greeks_vega=0.0,
            price_greeks_rho=0.0,
            price_greeks_omega=0.0,
            price_sensitivity=0.0,
            basis="",
            category="",
            currency_base="EUR",
            currency_profit="USD",
            currency_margin="USD",
            bank="",
            description="Euro vs US Dollar",
            exchange="",
            formula="",
            isin="",
            name="EURUSD",
            page="",
            path="Forex\\Majors\\EURUSD",
        )

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbol_info.return_value = mock_symbol

        client.initialize()
        dict_result = client.symbol_info_as_dict("EURUSD")

        assert isinstance(dict_result, dict)
        assert dict_result["name"] == "EURUSD"
        assert dict_result["digits"] == 5
        assert dict_result["bid"] == 1.13200
        assert dict_result["ask"] == 1.13210
        assert dict_result["currency_base"] == "EUR"
        assert dict_result["currency_profit"] == "USD"

    def test_symbol_info_tick_as_dict(self, mock_mt5_import: ModuleType | None) -> None:
        """Test symbol_info_tick_as_dict method."""
        assert mock_mt5_import is not None
        mock_tick = MockTick(
            time=1640995200,
            bid=1.13200,
            ask=1.13210,
            last=1.13205,
            volume=100,
            time_msc=1640995200123,
            flags=134,
            volume_real=100.0,
        )

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.symbol_info_tick.return_value = mock_tick

        client.initialize()
        dict_result = client.symbol_info_tick_as_dict("EURUSD")

        assert isinstance(dict_result, dict)
        assert dict_result["bid"] == 1.13200
        assert dict_result["ask"] == 1.13210
        assert dict_result["last"] == 1.13205
        assert dict_result["volume"] == 100
        assert dict_result["time"] == pd.to_datetime(1640995200, unit="s")
        assert dict_result["flags"] == 134

    def test_inheritance_behavior(self, mock_mt5_import: ModuleType | None) -> None:
        """Test that Mt5DataClient properly inherits from Mt5Client."""
        assert mock_mt5_import is not None
        client = Mt5DataClient(mt5=mock_mt5_import)

        assert isinstance(client, Mt5Client)

        # Test that Mt5DataClient has access to parent class methods
        assert hasattr(client, "initialize")
        assert hasattr(client, "shutdown")
        assert hasattr(client, "account_info")
        assert hasattr(client, "terminal_info")
        assert hasattr(client, "symbol_info")
        assert hasattr(client, "symbol_info_tick")
        assert hasattr(client, "copy_rates_from")
        assert hasattr(client, "copy_rates_from_pos")
        assert hasattr(client, "copy_rates_range")
        assert hasattr(client, "copy_ticks_from")
        assert hasattr(client, "copy_ticks_range")
        assert hasattr(client, "orders_get")
        assert hasattr(client, "positions_get")
        assert hasattr(client, "history_orders_get")
        assert hasattr(client, "history_deals_get")

        # Test that Mt5DataClient has its own methods
        assert hasattr(client, "account_info_as_df")
        assert hasattr(client, "terminal_info_as_df")
        assert hasattr(client, "copy_rates_from_as_df")
        assert hasattr(client, "copy_rates_from_pos_as_df")
        assert hasattr(client, "copy_rates_range_as_df")
        assert hasattr(client, "copy_ticks_from_as_df")
        assert hasattr(client, "copy_ticks_range_as_df")
        assert hasattr(client, "symbols_get_as_df")
        assert hasattr(client, "orders_get_as_df")
        assert hasattr(client, "positions_get_as_df")
        assert hasattr(client, "history_orders_get_as_df")
        assert hasattr(client, "history_deals_get_as_df")

        # Test that parent class methods work correctly
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.last_error.return_value = (0, "No error")

        result = client.initialize()
        assert result is True
        mock_mt5_import.initialize.assert_called_once()

        # Test last_error method from parent class
        error = client.last_error()
        assert error == (0, "No error")
        # last_error is called multiple times (in decorators and explicitly)
        assert mock_mt5_import.last_error.call_count >= 1

    def test_validate_history_input_with_ticket(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test _validate_history_input with ticket parameter."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Should not raise when ticket is provided
        client._validate_history_input(ticket=123456)

    def test_validate_history_input_with_position(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test _validate_history_input with position parameter."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Should not raise when position is provided
        client._validate_history_input(position=789012)

    def test_validate_history_input_with_dates(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test _validate_history_input with date parameters."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Should not raise when both dates are provided
        client._validate_history_input(
            date_from=datetime(2022, 1, 1, tzinfo=UTC),
            date_to=datetime(2022, 1, 2, tzinfo=UTC),
        )

    def test_validate_history_input_missing_date_to(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test _validate_history_input with missing date_to."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Should raise when only date_from is provided
        with pytest.raises(
            ValueError,
            match=(
                r"Both date_from and date_to must be provided"
                r" if not using ticket or position"
            ),
        ):
            client._validate_history_input(date_from=datetime(2022, 1, 1, tzinfo=UTC))

    def test_validate_history_input_missing_date_from(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test _validate_history_input with missing date_from."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Should raise when only date_to is provided
        with pytest.raises(
            ValueError,
            match=(
                r"Both date_from and date_to must be provided"
                r" if not using ticket or position"
            ),
        ):
            client._validate_history_input(date_to=datetime(2022, 1, 2, tzinfo=UTC))

    def test_validate_history_input_no_params(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test _validate_history_input with no parameters."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Should raise when no parameters are provided
        with pytest.raises(
            ValueError,
            match=(
                r"Both date_from and date_to must be provided"
                r" if not using ticket or position"
            ),
        ):
            client._validate_history_input()

    def test_history_deals_get_ticket_only(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_deals_get method with only ticket parameter."""
        assert mock_mt5_import is not None
        mock_deals = [
            MockDeal(
                ticket=123456,
                order=789012,
                time=1640995200,
                time_msc=1640995200000,
                type=0,
                entry=0,
                magic=0,
                position_id=345678,
                reason=0,
                volume=0.1,
                price=1.1300,
                commission=-2.5,
                swap=0.0,
                profit=10.0,
                fee=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_deals_get.return_value = mock_deals

        client.initialize()
        df_result = client.history_deals_get_as_df(ticket=123456, index_keys="ticket")

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.index[0] == 123456

    def test_history_deals_get_position_only(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test history_deals_get method with only position parameter."""
        assert mock_mt5_import is not None
        mock_deals = [
            MockDeal(
                ticket=123456,
                order=789012,
                time=1640995200,
                time_msc=1640995200000,
                type=0,
                entry=0,
                magic=0,
                position_id=345678,
                reason=0,
                volume=0.1,
                price=1.1300,
                commission=-2.5,
                swap=0.0,
                profit=10.0,
                fee=0.0,
                symbol="EURUSD",
                comment="",
                external_id="",
            ),
        ]

        client = Mt5DataClient(mt5=mock_mt5_import)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.history_deals_get.return_value = mock_deals

        client.initialize()
        df_result = client.history_deals_get_as_df(position=345678)

        assert isinstance(df_result, pd.DataFrame)
        assert len(df_result) == 1
        assert df_result.iloc[0]["position_id"] == 345678

    def test_context_manager_with_exception(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test context manager handles exceptions properly."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        test_exception_msg = "Test exception"
        with Mt5DataClient(mt5=mock_mt5_import) as client:
            assert client._is_initialized is True
            mock_mt5_import.initialize.assert_called_once()
            with pytest.raises(ValueError, match=test_exception_msg):
                raise ValueError(test_exception_msg)

        # Shutdown should still be called even with exception
        mock_mt5_import.shutdown.assert_called_once()

    def test_initialize_already_initialized_in_context(
        self, mock_mt5_import: ModuleType | None
    ) -> None:
        """Test initialize method when already initialized (covers line 70 exit)."""
        assert mock_mt5_import is not None
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        # First initialize the client normally
        result = client.initialize()
        assert result is True
        assert client._is_initialized is True
        mock_mt5_import.initialize.assert_called_once()

        # Reset the mock
        mock_mt5_import.initialize.reset_mock()

        # Call initialize again - should still call mt5.initialize()
        client.initialize()

        # Initialize should be called again in current implementation
        mock_mt5_import.initialize.assert_called_once()
        # The method should still return True (or whatever the expected behavior is)
        assert client._is_initialized is True


class TestMt5DataClientCoverageMissing:
    """Test class for missing coverage methods."""

    def test_version_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test version_as_df method."""
        mock_mt5_import.version.return_value = (123, 456, "build")
        mock_mt5_import.initialize.return_value = True
        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        result = client.version_as_df()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "mt5_terminal_version" in result.columns
        assert "build" in result.columns

    def test_last_error_as_dict(self, mock_mt5_import: ModuleType) -> None:
        """Test last_error_as_dict method."""
        mock_mt5_import.last_error.return_value = (123, "Test error")
        client = Mt5DataClient(mt5=mock_mt5_import)

        result = client.last_error_as_dict()

        assert isinstance(result, dict)
        assert result["error_code"] == 123
        assert result["error_description"] == "Test error"

    def test_last_error_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test last_error_as_df method."""
        mock_mt5_import.last_error.return_value = (456, "Another error")
        client = Mt5DataClient(mt5=mock_mt5_import)

        result = client.last_error_as_df()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "error_code" in result.columns
        assert "error_description" in result.columns
        assert result.iloc[0]["error_code"] == 456
        assert result.iloc[0]["error_description"] == "Another error"

    def test_symbol_info_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test symbol_info_as_df method."""

        class MockSymbolInfo(NamedTuple):
            symbol: str
            bid: float
            ask: float

        mock_symbol_info = MockSymbolInfo(symbol="EURUSD", bid=1.1000, ask=1.1001)
        mock_mt5_import.symbol_info.return_value = mock_symbol_info
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        result = client.symbol_info_as_df("EURUSD")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "symbol" in result.columns
        assert "bid" in result.columns
        assert "ask" in result.columns

    def test_symbol_info_tick_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test symbol_info_tick_as_df method."""

        class MockTick(NamedTuple):
            time: int
            bid: float
            ask: float

        mock_tick = MockTick(time=1640995200, bid=1.1000, ask=1.1001)
        mock_mt5_import.symbol_info_tick.return_value = mock_tick
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        result = client.symbol_info_tick_as_df("EURUSD")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "time" in result.columns
        assert "bid" in result.columns
        assert "ask" in result.columns

    def test_market_book_get_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test market_book_get_as_df method."""

        class MockBookInfo(NamedTuple):
            type: int
            price: float
            volume: float

        mock_book_data = [
            MockBookInfo(type=1, price=1.1000, volume=100.0),
            MockBookInfo(type=2, price=1.1001, volume=200.0),
        ]
        mock_mt5_import.market_book_get.return_value = mock_book_data
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        result = client.market_book_get_as_df("EURUSD", index_keys="price")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "type" in result.columns
        assert "volume" in result.columns
        # Price is used as index in market book data
        assert result.index.name == "price"

    def test_order_check_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test order_check_as_df method."""

        class MockRequest(NamedTuple):
            action: int
            symbol: str

        class MockOrderCheck(NamedTuple):
            retcode: int
            margin: float
            profit: float
            request: MockRequest

        mock_request = MockRequest(action=1, symbol="EURUSD")
        mock_order_check = MockOrderCheck(
            retcode=10009, margin=100.0, profit=50.0, request=mock_request
        )
        mock_mt5_import.order_check.return_value = mock_order_check
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        request = {"action": 1, "symbol": "EURUSD", "volume": 0.1}
        result = client.order_check_as_df(request)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "retcode" in result.columns
        assert "margin" in result.columns
        assert "profit" in result.columns

    def test_order_send_as_df(self, mock_mt5_import: ModuleType) -> None:
        """Test order_send_as_df method."""

        class MockRequest(NamedTuple):
            action: int
            symbol: str

        class MockOrderSend(NamedTuple):
            retcode: int
            deal: int
            order: int
            request: MockRequest

        mock_request = MockRequest(action=1, symbol="EURUSD")
        mock_order_send = MockOrderSend(
            retcode=10009, deal=12345, order=67890, request=mock_request
        )
        mock_mt5_import.order_send.return_value = mock_order_send
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        request = {"action": 1, "symbol": "EURUSD", "volume": 0.1}
        result = client.order_send_as_df(request)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert "retcode" in result.columns
        assert "deal" in result.columns
        assert "order" in result.columns

    def test_flatten_dict_to_one_level_simple(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test _flatten_dict_to_one_level with simple dict."""
        client = Mt5DataClient(mt5=mock_mt5_import)

        input_dict = {"a": 1, "b": 2, "c": 3}
        result = client._flatten_dict_to_one_level(input_dict)

        assert result == {"a": 1, "b": 2, "c": 3}

    def test_flatten_dict_to_one_level_nested(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test _flatten_dict_to_one_level with nested dict."""
        client = Mt5DataClient(mt5=mock_mt5_import)

        input_dict = {
            "a": 1,
            "nested": {"x": 10, "y": 20},
            "b": 2,
        }
        result = client._flatten_dict_to_one_level(input_dict)

        assert result == {"a": 1, "nested_x": 10, "nested_y": 20, "b": 2}

    def test_flatten_dict_to_one_level_custom_separator(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test _flatten_dict_to_one_level with custom separator."""
        client = Mt5DataClient(mt5=mock_mt5_import)

        input_dict = {
            "level1": {"level2": {"level3": "value"}},
            "simple": "value2",
        }
        result = client._flatten_dict_to_one_level(input_dict, sep="_")

        assert result == {"level1_level2": {"level3": "value"}, "simple": "value2"}

    def test_symbols_get_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test symbols_get_as_dicts method."""

        # Create a minimal mock symbol with required fields
        class MockSymbol:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "name": "EURUSD",
                    "time": 1640995200,
                    "time_msc": 1640995200000,
                    "time_digits": 1640995200,
                    "bid": 1.1300,
                    "ask": 1.1301,
                }

        mock_symbol = MockSymbol()
        mock_mt5_import.symbols_get.return_value = [mock_symbol]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        # Test without convert_time
        result = client.symbols_get_as_dicts(skip_to_datetime=True)
        assert len(result) == 1
        assert result[0]["name"] == "EURUSD"
        assert result[0]["time"] == 1640995200
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.symbols_get_as_dicts()
        assert len(result) == 1
        assert result[0]["name"] == "EURUSD"
        # Note: Time conversion behavior through decorators needs validation
        # For now, just check the result is valid
        assert "time" in result[0]
        assert "time_msc" in result[0]

    def test_symbols_get_as_df_with_params(self, mock_mt5_import: ModuleType) -> None:
        """Test symbols_get_as_df with new parameters."""

        # Create a minimal mock symbol with required fields
        class MockSymbol:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "name": "EURUSD",
                    "time": 1640995200,
                    "time_msc": 1640995200000,
                    "time_digits": 1640995200,
                    "bid": 1.1300,
                    "ask": 1.1301,
                }

        mock_symbol = MockSymbol()
        mock_mt5_import.symbols_get.return_value = [mock_symbol]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test with skip_to_datetime=True
        result = client.symbols_get_as_df(skip_to_datetime=True)
        assert isinstance(result["time"].iloc[0], (int, np.integer))
        assert result.index.name is None

        # Test with skip_to_datetime=False and index_keys
        result = client.symbols_get_as_df(skip_to_datetime=False, index_keys="name")
        assert "time" in result.columns
        assert result.index.name == "name"
        assert "EURUSD" in result.index

    def test_symbol_info_as_dict_with_skip_to_datetime(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test symbol_info_as_dict with skip_to_datetime parameter."""

        # Create a minimal mock symbol with required fields
        class MockSymbol:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "name": "EURUSD",
                    "time": 1640995200,
                    "time_msc": 1640995200000,
                    "time_digits": 1640995200,
                    "bid": 1.1300,
                    "ask": 1.1301,
                }

        mock_symbol = MockSymbol()
        mock_mt5_import.symbol_info.return_value = mock_symbol
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test with skip_to_datetime=True
        result = client.symbol_info_as_dict("EURUSD", skip_to_datetime=True)
        assert result["time"] == 1640995200
        assert isinstance(result["time"], int)

        # Test with convert_time=True (default)
        result = client.symbol_info_as_dict("EURUSD")
        assert "time" in result
        assert "time_msc" in result

    def test_symbol_info_tick_as_dict_with_skip_to_datetime(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test symbol_info_tick_as_dict with skip_to_datetime parameter."""
        mock_tick = MockTick(
            time=1640995200,
            bid=1.1300,
            ask=1.1301,
            last=0,
            volume=0,
            time_msc=1640995200000,
            flags=0,
            volume_real=0,
        )
        mock_mt5_import.symbol_info_tick.return_value = mock_tick
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test with skip_to_datetime=True
        result = client.symbol_info_tick_as_dict("EURUSD", skip_to_datetime=True)
        assert result["time"] == 1640995200
        assert isinstance(result["time"], int)

        # Test with convert_time=True (default)
        result = client.symbol_info_tick_as_dict("EURUSD")
        assert "time" in result
        assert "time_msc" in result

    def test_market_book_get_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test market_book_get_as_dicts method."""
        mock_book_entry = MockBookInfo(
            type=0,
            price=1.1300,
            volume=100.0,
            volume_real=100.0,
        )
        mock_mt5_import.market_book_get.return_value = [mock_book_entry]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test without convert_time
        result = client.market_book_get_as_dicts("EURUSD", skip_to_datetime=True)
        assert len(result) == 1
        assert result[0]["price"] == 1.1300
        assert result[0]["type"] == 0

        # Test with convert_time (default True)
        result = client.market_book_get_as_dicts("EURUSD")
        assert len(result) == 1
        assert result[0]["price"] == 1.1300
        assert result[0]["type"] == 0

    def test_copy_rates_from_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test copy_rates_from_as_dicts method."""
        rate_dtype = np.dtype([
            ("time", "int64"),
            ("open", "float64"),
            ("high", "float64"),
            ("low", "float64"),
            ("close", "float64"),
        ])
        mock_rates = np.array(
            [(1640995200, 1.1300, 1.1350, 1.1280, 1.1320)],
            dtype=rate_dtype,
        )
        mock_mt5_import.copy_rates_from.return_value = mock_rates
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test without convert_time
        result = client.copy_rates_from_as_dicts(
            "EURUSD", 16385, datetime(2023, 1, 1, tzinfo=UTC), 10, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["time"] == 1640995200
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.copy_rates_from_as_dicts(
            "EURUSD", 16385, datetime(2023, 1, 1, tzinfo=UTC), 10
        )
        assert len(result) == 1
        assert "time" in result[0]

    def test_copy_rates_from_pos_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test copy_rates_from_pos_as_dicts method."""
        rate_dtype = np.dtype([
            ("time", "int64"),
            ("open", "float64"),
            ("high", "float64"),
            ("low", "float64"),
            ("close", "float64"),
        ])
        mock_rates = np.array(
            [(1640995200, 1.1300, 1.1350, 1.1280, 1.1320)],
            dtype=rate_dtype,
        )
        mock_mt5_import.copy_rates_from_pos.return_value = mock_rates
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test without convert_time
        result = client.copy_rates_from_pos_as_dicts(
            "EURUSD", 16385, 0, 10, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["time"] == 1640995200
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.copy_rates_from_pos_as_dicts("EURUSD", 16385, 0, 10)
        assert len(result) == 1
        assert "time" in result[0]

    def test_copy_rates_range_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test copy_rates_range_as_dicts method."""
        rate_dtype = np.dtype([
            ("time", "int64"),
            ("open", "float64"),
            ("high", "float64"),
            ("low", "float64"),
            ("close", "float64"),
        ])
        mock_rates = np.array(
            [(1640995200, 1.1300, 1.1350, 1.1280, 1.1320)],
            dtype=rate_dtype,
        )
        mock_mt5_import.copy_rates_range.return_value = mock_rates
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        date_from = datetime(2023, 1, 1, tzinfo=UTC)
        date_to = datetime(2023, 1, 2, tzinfo=UTC)

        # Test without convert_time
        result = client.copy_rates_range_as_dicts(
            "EURUSD", 16385, date_from, date_to, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["time"] == 1640995200
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.copy_rates_range_as_dicts("EURUSD", 16385, date_from, date_to)
        assert len(result) == 1
        assert "time" in result[0]

    def test_copy_ticks_from_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test copy_ticks_from_as_dicts method."""
        tick_dtype = np.dtype([
            ("time", "int64"),
            ("bid", "float64"),
            ("ask", "float64"),
            ("last", "float64"),
            ("volume", "uint64"),
            ("time_msc", "int64"),
            ("flags", "uint32"),
            ("volume_real", "float64"),
        ])
        mock_ticks = np.array(
            [(1640995200, 1.1300, 1.1301, 0, 0, 1640995200000, 0, 0)],
            dtype=tick_dtype,
        )
        mock_mt5_import.copy_ticks_from.return_value = mock_ticks
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test without convert_time
        result = client.copy_ticks_from_as_dicts(
            "EURUSD", datetime(2023, 1, 1, tzinfo=UTC), 10, 0, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["time"] == 1640995200
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.copy_ticks_from_as_dicts(
            "EURUSD", datetime(2023, 1, 1, tzinfo=UTC), 10, 0
        )
        assert len(result) == 1
        assert "time" in result[0]
        assert "time_msc" in result[0]

    def test_copy_ticks_range_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test copy_ticks_range_as_dicts method."""
        tick_dtype = np.dtype([
            ("time", "int64"),
            ("bid", "float64"),
            ("ask", "float64"),
            ("last", "float64"),
            ("volume", "uint64"),
            ("time_msc", "int64"),
            ("flags", "uint32"),
            ("volume_real", "float64"),
        ])
        mock_ticks = np.array(
            [(1640995200, 1.1300, 1.1301, 0, 0, 1640995200000, 0, 0)],
            dtype=tick_dtype,
        )
        mock_mt5_import.copy_ticks_range.return_value = mock_ticks
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        date_from = datetime(2023, 1, 1, tzinfo=UTC)
        date_to = datetime(2023, 1, 2, tzinfo=UTC)

        # Test without convert_time
        result = client.copy_ticks_range_as_dicts(
            "EURUSD", date_from, date_to, 0, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["time"] == 1640995200
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.copy_ticks_range_as_dicts("EURUSD", date_from, date_to, 0)
        assert len(result) == 1
        assert "time" in result[0]
        assert "time_msc" in result[0]

    def test_orders_get_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test orders_get_as_dicts method."""
        mock_order = MockOrder(
            ticket=12345,
            time_setup=1640995200,
            time_setup_msc=1640995200000,
            time_done=0,
            time_done_msc=0,
            time_expiration=1640995200,
            type=0,
            type_time=0,
            type_filling=0,
            state=1,
            magic=0,
            position_id=0,
            position_by_id=0,
            reason=0,
            volume_initial=0.1,
            volume_current=0.1,
            price_open=1.1300,
            sl=1.1200,
            tp=1.1400,
            price_current=1.1301,
            price_stoplimit=0.0,
            symbol="EURUSD",
            comment="",
            external_id="",
        )
        mock_mt5_import.orders_get.return_value = [mock_order]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test without convert_time
        result = client.orders_get_as_dicts(skip_to_datetime=True)
        assert len(result) == 1
        assert result[0]["ticket"] == 12345
        assert isinstance(result[0]["time_setup"], int)

        # Test with convert_time (default True)
        result = client.orders_get_as_dicts()
        assert len(result) == 1
        assert "time_setup" in result[0]
        assert "time_setup_msc" in result[0]

    def test_positions_get_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test positions_get_as_dicts method."""
        mock_position = MockPosition(
            ticket=12345,
            time=1640995200,
            time_msc=1640995200000,
            time_update=1640995200,
            time_update_msc=1640995200000,
            type=0,
            magic=0,
            identifier=0,
            reason=0,
            volume=0.1,
            price_open=1.1300,
            sl=1.1200,
            tp=1.1400,
            price_current=1.1301,
            swap=0.0,
            profit=0.0,
            symbol="EURUSD",
            comment="",
            external_id="",
        )
        mock_mt5_import.positions_get.return_value = [mock_position]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test without convert_time
        result = client.positions_get_as_dicts(skip_to_datetime=True)
        assert len(result) == 1
        assert result[0]["ticket"] == 12345
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.positions_get_as_dicts()
        assert len(result) == 1
        assert "time" in result[0]
        assert "time_msc" in result[0]

    def test_history_orders_get_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test history_orders_get_as_dicts method."""
        mock_order = MockOrder(
            ticket=12345,
            time_setup=1640995200,
            time_setup_msc=1640995200000,
            time_done=1640995200,
            time_done_msc=1640995200000,
            time_expiration=0,
            type=0,
            type_time=0,
            type_filling=0,
            state=1,
            magic=0,
            position_id=0,
            position_by_id=0,
            reason=0,
            volume_initial=0.1,
            volume_current=0.1,
            price_open=1.1300,
            sl=1.1200,
            tp=1.1400,
            price_current=1.1301,
            price_stoplimit=0.0,
            symbol="EURUSD",
            comment="",
            external_id="",
        )
        mock_mt5_import.history_orders_get.return_value = [mock_order]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        date_from = datetime(2023, 1, 1, tzinfo=UTC)
        date_to = datetime(2023, 1, 2, tzinfo=UTC)

        # Test without convert_time
        result = client.history_orders_get_as_dicts(
            date_from=date_from, date_to=date_to, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["ticket"] == 12345
        assert isinstance(result[0]["time_setup"], int)

        # Test with convert_time (default True)
        result = client.history_orders_get_as_dicts(
            date_from=date_from, date_to=date_to
        )
        assert len(result) == 1
        assert "time_setup" in result[0]
        assert "time_done_msc" in result[0]

    def test_history_deals_get_as_dicts(self, mock_mt5_import: ModuleType) -> None:
        """Test history_deals_get_as_dicts method."""
        mock_deal = MockDeal(
            ticket=12345,
            order=0,
            time=1640995200,
            time_msc=1640995200000,
            type=0,
            entry=0,
            magic=0,
            position_id=0,
            reason=0,
            volume=0.1,
            price=1.1300,
            commission=0.0,
            swap=0.0,
            profit=0.0,
            fee=0.0,
            symbol="EURUSD",
            comment="",
            external_id="",
        )
        mock_mt5_import.history_deals_get.return_value = [mock_deal]
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()
        date_from = datetime(2023, 1, 1, tzinfo=UTC)
        date_to = datetime(2023, 1, 2, tzinfo=UTC)

        # Test without convert_time
        result = client.history_deals_get_as_dicts(
            date_from=date_from, date_to=date_to, skip_to_datetime=True
        )
        assert len(result) == 1
        assert result[0]["ticket"] == 12345
        assert isinstance(result[0]["time"], int)

        # Test with convert_time (default True)
        result = client.history_deals_get_as_dicts(date_from=date_from, date_to=date_to)
        assert len(result) == 1
        assert "time" in result[0]
        assert "time_msc" in result[0]

    def test_dataframe_methods_with_index_keys(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test all DataFrame methods with index_keys parameter."""
        mock_mt5_import.initialize.return_value = True
        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test copy_rates_from_as_df with index_keys
        rate_dtype = np.dtype([
            ("time", "int64"),
            ("open", "float64"),
            ("high", "float64"),
            ("low", "float64"),
            ("close", "float64"),
        ])
        mock_rates = np.array(
            [(1640995200, 1.1300, 1.1350, 1.1280, 1.1320)],
            dtype=rate_dtype,
        )
        mock_mt5_import.copy_rates_from.return_value = mock_rates

        result = client.copy_rates_from_as_df(
            "EURUSD", 16385, datetime(2023, 1, 1, tzinfo=UTC), 10, index_keys="time"
        )
        assert result.index.name == "time"
        assert pd.to_datetime(1640995200, unit="s") in result.index

        # Test copy_ticks_from_as_df with index_keys
        tick_dtype = np.dtype([
            ("time", "int64"),
            ("bid", "float64"),
            ("ask", "float64"),
            ("last", "float64"),
            ("volume", "uint64"),
            ("time_msc", "int64"),
            ("flags", "uint32"),
            ("volume_real", "float64"),
        ])
        mock_ticks = np.array(
            [(1640995200, 1.1300, 1.1301, 0, 0, 1640995200000, 0, 0)],
            dtype=tick_dtype,
        )
        mock_mt5_import.copy_ticks_from.return_value = mock_ticks

        result = client.copy_ticks_from_as_df(
            "EURUSD", datetime(2023, 1, 1, tzinfo=UTC), 10, 0, index_keys="time_msc"
        )
        assert result.index.name == "time_msc"
        assert pd.to_datetime(1640995200000, unit="ms") in result.index

        # Test orders_get_as_df with index_keys
        mock_order = MockOrder(
            ticket=12345,
            time_setup=1640995200,
            time_setup_msc=1640995200000,
            time_done=0,
            time_done_msc=0,
            time_expiration=0,
            type=0,
            type_time=0,
            type_filling=0,
            state=1,
            magic=0,
            position_id=0,
            position_by_id=0,
            reason=0,
            volume_initial=0.1,
            volume_current=0.1,
            price_open=1.1300,
            sl=1.1200,
            tp=1.1400,
            price_current=1.1301,
            price_stoplimit=0.0,
            symbol="EURUSD",
            comment="",
            external_id="",
        )
        mock_mt5_import.orders_get.return_value = [mock_order]

        result = client.orders_get_as_df(index_keys="ticket")
        assert result.index.name == "ticket"
        assert 12345 in result.index

        # Test positions_get_as_df with index_keys
        mock_position = MockPosition(
            ticket=54321,
            time=1640995200,
            time_msc=1640995200000,
            time_update=1640995200,
            time_update_msc=1640995200000,
            type=0,
            magic=0,
            identifier=0,
            reason=0,
            volume=0.1,
            price_open=1.1300,
            sl=1.1200,
            tp=1.1400,
            price_current=1.1301,
            swap=0.0,
            profit=0.0,
            symbol="EURUSD",
            comment="",
            external_id="",
        )
        mock_mt5_import.positions_get.return_value = [mock_position]

        result = client.positions_get_as_df(index_keys="ticket")
        assert result.index.name == "ticket"
        assert 54321 in result.index

        # Test empty DataFrame doesn't set index
        mock_mt5_import.orders_get.return_value = []
        result = client.orders_get_as_df(index_keys="ticket")
        assert result.empty
        assert result.index.name is None

    def test_set_index_if_possible_decorator(self, mock_mt5_import: ModuleType) -> None:
        """Test set_index_if_possible decorator behavior."""
        client = Mt5DataClient(mt5=mock_mt5_import)

        # Mock symbol data
        class MockSymbol:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "name": "EURUSD",
                    "time": 1640995200,
                    "bid": 1.1300,
                    "ask": 1.1301,
                }

        mock_symbol = MockSymbol()
        mock_mt5_import.symbols_get.return_value = [mock_symbol]
        mock_mt5_import.initialize.return_value = True

        client.initialize()

        # Test with index_keys=None (should not set index)
        result = client.symbols_get_as_df(index_keys=None)
        assert result.index.name is None

        # Test with empty DataFrame (should not set index even with index_keys)
        mock_mt5_import.symbols_get.return_value = []
        result = client.symbols_get_as_df(index_keys="name")
        assert result.empty
        assert result.index.name is None

    def test_detect_and_convert_time_decorator(
        self, mock_mt5_import: ModuleType
    ) -> None:
        """Test detect_and_convert_time_to_datetime decorator behavior."""
        mock_mt5_import.initialize.return_value = True
        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # Test with dict result
        class MockSymbol:
            def _asdict(self) -> dict[str, Any]:
                return {
                    "name": "EURUSD",
                    "time": 1640995200,
                    "time_msc": 1640995200000,
                    "bid": 1.1300,
                    "ask": 1.1301,
                }

        mock_symbol = MockSymbol()
        mock_mt5_import.symbol_info.return_value = mock_symbol

        # With convert_time=True (default)
        result = client.symbol_info_as_dict("EURUSD")
        assert "time" in result

        # With skip_to_datetime=True
        result = client.symbol_info_as_dict("EURUSD", skip_to_datetime=True)
        assert isinstance(result["time"], int)

        # Test with list result
        mock_mt5_import.symbols_get.return_value = [mock_symbol]

        result = client.symbols_get_as_dicts()
        assert "time" in result[0]

        result = client.symbols_get_as_dicts(skip_to_datetime=True)
        assert isinstance(result[0]["time"], int)

    def test_detect_and_convert_time_decorator_list_return(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test detect_and_convert_time decorator with list return value."""
        # Mock a method that returns a list
        mock_symbols = [
            MockSymbolInfo(
                custom=False,
                chart_mode=0,
                select=True,
                visible=True,
                session_deals=0,
                session_buy_orders=0,
                session_sell_orders=0,
                volume=0,
                volumehigh=0,
                volumelow=0,
                time=1640995200,
                digits=5,
                spread=10,
                spread_float=True,
                ticks_bookdepth=10,
                trade_calc_mode=0,
                trade_mode=4,
                start_time=0,
                expiration_time=0,
                trade_stops_level=0,
                trade_freeze_level=0,
                trade_exemode=1,
                swap_mode=1,
                swap_rollover3days=3,
                margin_hedged_use_leg=False,
                expiration_mode=7,
                filling_mode=1,
                order_mode=127,
                order_gtc_mode=0,
                option_mode=0,
                option_right=0,
                bid=1.13200,
                bidhigh=1.13500,
                bidlow=1.13000,
                ask=1.13210,
                askhigh=1.13510,
                asklow=1.13010,
                last=1.13205,
                lasthigh=1.13505,
                lastlow=1.13005,
                volume_real=1000000.0,
                volumehigh_real=2000000.0,
                volumelow_real=500000.0,
                option_strike=0.0,
                point=0.00001,
                trade_tick_value=1.0,
                trade_tick_value_profit=1.0,
                trade_tick_value_loss=1.0,
                trade_tick_size=0.00001,
                trade_contract_size=100000.0,
                trade_accrued_interest=0.0,
                trade_face_value=0.0,
                trade_liquidity_rate=0.0,
                volume_min=0.01,
                volume_max=500.0,
                volume_step=0.01,
                volume_limit=0.0,
                swap_long=-0.5,
                swap_short=-0.3,
                margin_initial=0.0,
                margin_maintenance=0.0,
                session_volume=0.0,
                session_turnover=0.0,
                session_interest=0.0,
                session_buy_orders_volume=0.0,
                session_sell_orders_volume=0.0,
                session_open=1.13100,
                session_close=1.13200,
                session_aw=0.0,
                session_price_settlement=0.0,
                session_price_limit_min=0.0,
                session_price_limit_max=0.0,
                margin_hedged=50000.0,
                price_change=0.0010,
                price_volatility=0.0,
                price_theoretical=0.0,
                price_greeks_delta=0.0,
                price_greeks_theta=0.0,
                price_greeks_gamma=0.0,
                price_greeks_vega=0.0,
                price_greeks_rho=0.0,
                price_greeks_omega=0.0,
                price_sensitivity=0.0,
                basis="",
                category="",
                currency_base="EUR",
                currency_profit="USD",
                currency_margin="USD",
                bank="",
                description="Euro vs US Dollar",
                exchange="",
                formula="",
                isin="",
                name="EURUSD",
                page="",
                path="Forex\\Majors\\EURUSD",
            )
        ]

        mock_mt5_import.symbols_get.return_value = mock_symbols
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # This should trigger the list processing path
        result = client.symbols_get_as_dicts()
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert "time" in result[0]

    def test_detect_and_convert_time_decorator_non_dict_object(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test detect_and_convert_time decorator with non-dict return value."""
        # Mock a method that returns a non-dict, non-list, non-DataFrame object
        mock_mt5_import.symbols_total.return_value = 42
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # This should trigger the else path
        result = client.symbols_total()
        assert result == 42  # Should return unchanged

    def test_convert_time_decorator_dict_return_with_convert_time_true(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test detect_and_convert_time decorator with dict return."""
        # This test specifically targets early return for datetime
        mock_symbol = MockSymbolInfo(
            custom=False,
            chart_mode=0,
            select=True,
            visible=True,
            session_deals=0,
            session_buy_orders=0,
            session_sell_orders=0,
            volume=0,
            volumehigh=0,
            volumelow=0,
            time=1640995200,
            digits=5,
            spread=10,
            spread_float=True,
            ticks_bookdepth=10,
            trade_calc_mode=0,
            trade_mode=4,
            start_time=0,
            expiration_time=0,
            trade_stops_level=0,
            trade_freeze_level=0,
            trade_exemode=1,
            swap_mode=1,
            swap_rollover3days=3,
            margin_hedged_use_leg=False,
            expiration_mode=7,
            filling_mode=1,
            order_mode=127,
            order_gtc_mode=0,
            option_mode=0,
            option_right=0,
            bid=1.13200,
            bidhigh=1.13500,
            bidlow=1.13000,
            ask=1.13210,
            askhigh=1.13510,
            asklow=1.13010,
            last=1.13205,
            lasthigh=1.13505,
            lastlow=1.13005,
            volume_real=1000000.0,
            volumehigh_real=2000000.0,
            volumelow_real=500000.0,
            option_strike=0.0,
            point=0.00001,
            trade_tick_value=1.0,
            trade_tick_value_profit=1.0,
            trade_tick_value_loss=1.0,
            trade_tick_size=0.00001,
            trade_contract_size=100000.0,
            trade_accrued_interest=0.0,
            trade_face_value=0.0,
            trade_liquidity_rate=0.0,
            volume_min=0.01,
            volume_max=500.0,
            volume_step=0.01,
            volume_limit=0.0,
            swap_long=-0.5,
            swap_short=-0.3,
            margin_initial=0.0,
            margin_maintenance=0.0,
            session_volume=0.0,
            session_turnover=0.0,
            session_interest=0.0,
            session_buy_orders_volume=0.0,
            session_sell_orders_volume=0.0,
            session_open=1.13100,
            session_close=1.13200,
            session_aw=0.0,
            session_price_settlement=0.0,
            session_price_limit_min=0.0,
            session_price_limit_max=0.0,
            margin_hedged=50000.0,
            price_change=0.0010,
            price_volatility=0.0,
            price_theoretical=0.0,
            price_greeks_delta=0.0,
            price_greeks_theta=0.0,
            price_greeks_gamma=0.0,
            price_greeks_vega=0.0,
            price_greeks_rho=0.0,
            price_greeks_omega=0.0,
            price_sensitivity=0.0,
            basis="",
            category="",
            currency_base="EUR",
            currency_profit="USD",
            currency_margin="USD",
            bank="",
            description="Euro vs US Dollar",
            exchange="",
            formula="",
            isin="",
            name="EURUSD",
            page="",
            path="Forex\\Majors\\EURUSD",
        )

        mock_mt5_import.symbol_info.return_value = mock_symbol
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # This should trigger return _convert_time_values_in_dict()
        result = client.symbol_info_as_dict("EURUSD", skip_to_datetime=False)
        assert isinstance(result, dict)
        assert "time" in result
        # Check that time was converted to datetime
        assert isinstance(result["time"], pd.Timestamp)

    def test_convert_time_decorator_list_with_dicts_convert_time_true(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test detect_and_convert_time decorator with list of dicts."""
        # This test specifically targets dict processing
        mock_symbols = [
            MockSymbolInfo(
                custom=False,
                chart_mode=0,
                select=True,
                visible=True,
                session_deals=0,
                session_buy_orders=0,
                session_sell_orders=0,
                volume=0,
                volumehigh=0,
                volumelow=0,
                time=1640995200,
                digits=5,
                spread=10,
                spread_float=True,
                ticks_bookdepth=10,
                trade_calc_mode=0,
                trade_mode=4,
                start_time=0,
                expiration_time=0,
                trade_stops_level=0,
                trade_freeze_level=0,
                trade_exemode=1,
                swap_mode=1,
                swap_rollover3days=3,
                margin_hedged_use_leg=False,
                expiration_mode=7,
                filling_mode=1,
                order_mode=127,
                order_gtc_mode=0,
                option_mode=0,
                option_right=0,
                bid=1.13200,
                bidhigh=1.13500,
                bidlow=1.13000,
                ask=1.13210,
                askhigh=1.13510,
                asklow=1.13010,
                last=1.13205,
                lasthigh=1.13505,
                lastlow=1.13005,
                volume_real=1000000.0,
                volumehigh_real=2000000.0,
                volumelow_real=500000.0,
                option_strike=0.0,
                point=0.00001,
                trade_tick_value=1.0,
                trade_tick_value_profit=1.0,
                trade_tick_value_loss=1.0,
                trade_tick_size=0.00001,
                trade_contract_size=100000.0,
                trade_accrued_interest=0.0,
                trade_face_value=0.0,
                trade_liquidity_rate=0.0,
                volume_min=0.01,
                volume_max=500.0,
                volume_step=0.01,
                volume_limit=0.0,
                swap_long=-0.5,
                swap_short=-0.3,
                margin_initial=0.0,
                margin_maintenance=0.0,
                session_volume=0.0,
                session_turnover=0.0,
                session_interest=0.0,
                session_buy_orders_volume=0.0,
                session_sell_orders_volume=0.0,
                session_open=1.13100,
                session_close=1.13200,
                session_aw=0.0,
                session_price_settlement=0.0,
                session_price_limit_min=0.0,
                session_price_limit_max=0.0,
                margin_hedged=50000.0,
                price_change=0.0010,
                price_volatility=0.0,
                price_theoretical=0.0,
                price_greeks_delta=0.0,
                price_greeks_theta=0.0,
                price_greeks_gamma=0.0,
                price_greeks_vega=0.0,
                price_greeks_rho=0.0,
                price_greeks_omega=0.0,
                price_sensitivity=0.0,
                basis="",
                category="",
                currency_base="EUR",
                currency_profit="USD",
                currency_margin="USD",
                bank="",
                description="Euro vs US Dollar",
                exchange="",
                formula="",
                isin="",
                name="EURUSD",
                page="",
                path="Forex\\Majors\\EURUSD",
            )
        ]

        mock_mt5_import.symbols_get.return_value = mock_symbols
        mock_mt5_import.initialize.return_value = True

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # This should trigger the list comprehension with dict processing
        result = client.symbols_get_as_dicts(skip_to_datetime=False)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert "time" in result[0]
        # Check that time was converted to datetime
        assert isinstance(result[0]["time"], pd.Timestamp)

    def test_convert_time_decorator_non_standard_return_type(
        self,
        mock_mt5_import: ModuleType,
    ) -> None:
        """Test detect_and_convert_time decorator with non-standard return type."""
        # This test specifically targets return result (else case)

        # Mock a method that returns a string (not dict, list, or DataFrame)
        mock_mt5_import.initialize.return_value = True
        mock_mt5_import.version.return_value = (123, 456, "2024-01-01")  # returns tuple

        client = Mt5DataClient(mt5=mock_mt5_import)
        client.initialize()

        # version() returns a tuple, which should trigger the else clause
        result = client.version()
        assert isinstance(result, tuple)
        assert result == (123, 456, "2024-01-01")  # Should return unchanged

    def test_convert_time_decorator_string_return_type(self) -> None:
        """Test detect_and_convert_time decorator with string return type."""
        # This test specifically targets return result (else case)

        @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
        def mock_function_returning_string(skip_to_datetime: bool = False) -> str:  # noqa: ARG001
            """Mock function that returns a string."""
            return "test_string"  # Return string instead of dict/list/DataFrame

        # Call with skip_to_datetime=False (should trigger else clause)
        result = mock_function_returning_string(skip_to_datetime=False)
        assert result == "test_string"  # Should return unchanged

        # Call with skip_to_datetime=True (should trigger early return)
        result = mock_function_returning_string(skip_to_datetime=True)
        assert result == "test_string"  # Should return unchanged
