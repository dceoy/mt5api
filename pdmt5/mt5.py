"""MetaTrader5 client wrapper class."""

# ruff: noqa: ANN401

from __future__ import annotations

import importlib
import logging
from functools import wraps
from types import ModuleType  # noqa: TC003
from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from types import TracebackType


class Mt5RuntimeError(RuntimeError):
    """MetaTrader5 specific runtime error.

    Raised when MetaTrader5 operations fail or when the client
    is used incorrectly (e.g., calling methods before initialization).
    """


class Mt5Client(BaseModel):
    """MetaTrader5 client class.

    This class provides a wrapper interface to all MetaTrader5 functions,
    delegating calls to the underlying MetaTrader5 module while providing
    error handling and logging capabilities.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    mt5: ModuleType = Field(
        default_factory=lambda: importlib.import_module("MetaTrader5"),
        description="MetaTrader5 module instance",
    )
    logger: logging.Logger = Field(
        default_factory=lambda: logging.getLogger(__name__),
        description="Logger instance for MetaTrader5 operations",
    )
    _is_initialized: bool = False

    @staticmethod
    def _log_mt5_last_status_code(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to log MetaTrader5 last status code after method execution.

        Args:
            func: The method to decorate.

        Returns:
            The decorated method.
        """

        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                response = func(self, *args, **kwargs)
            except Exception as e:
                error_message = f"MT5 {func.__name__} failed with error: {e}"
                raise Mt5RuntimeError(error_message) from e
            else:
                self.logger.info(
                    "MT5 %s returned a response: %s",
                    func.__name__,
                    response,
                )
                return response
            finally:
                last_error_response = self.mt5.last_error()
                message = f"MT5 last status: {last_error_response}"
                if last_error_response[0] != self.mt5.RES_S_OK:
                    self.logger.warning(message)
                else:
                    self.logger.info(message)

        return wrapper

    def __enter__(self) -> Self:
        """Context manager entry.

        Returns:
            Mt5Client: The client instance.
        """
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.shutdown()

    @_log_mt5_last_status_code
    def initialize(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        timeout: int | None = None,
    ) -> bool:
        """Establish a connection with the MetaTrader 5 terminal.

        Args:
            path: Path to the MetaTrader 5 terminal EXE file.
            login: Trading account number.
            password: Trading account password.
            server: Trade server address.
            timeout: Connection timeout in milliseconds.

        Returns:
            True if successful, False otherwise.
        """
        if path is not None:
            self.logger.info(
                "Initializing MT5 connection with path: %s",
                path,
            )
            self._is_initialized = self.mt5.initialize(
                path,
                **{
                    k: v
                    for k, v in {
                        "login": login,
                        "password": password,
                        "server": server,
                        "timeout": timeout,
                    }.items()
                    if v is not None
                },
            )
        else:
            self.logger.info("Initializing MT5 connection.")
            self._is_initialized = self.mt5.initialize()
        return self._is_initialized

    @_log_mt5_last_status_code
    def login(
        self,
        login: int,
        password: str | None = None,
        server: str | None = None,
        timeout: int | None = None,
    ) -> bool:
        """Connect to a trading account using specified parameters.

        Args:
            login: Trading account number.
            password: Trading account password.
            server: Trade server address.
            timeout: Connection timeout in milliseconds.

        Returns:
            True if successful, False otherwise.
        """
        self._initialize_if_needed()
        self.logger.info("Logging in to MT5 account: %d", login)
        return self.mt5.login(
            login,
            **{
                k: v
                for k, v in {
                    "password": password,
                    "server": server,
                    "timeout": timeout,
                }.items()
                if v is not None
            },
        )

    @_log_mt5_last_status_code
    def shutdown(self) -> None:
        """Close the previously established connection to the MetaTrader 5 terminal."""
        self.logger.info("Shutting down MT5 connection.")
        response = self.mt5.shutdown()
        self._is_initialized = False
        return response

    @_log_mt5_last_status_code
    def version(self) -> tuple[int, int, str]:
        """Return the MetaTrader 5 terminal version.

        Returns:
            Tuple of (terminal_version, build, release_date).
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving MT5 version information.")
        return self.mt5.version()

    @_log_mt5_last_status_code
    def last_error(self) -> tuple[int, str]:
        """Return data on the last error.

        Returns:
            Tuple of (error_code, error_description).
        """
        self.logger.info("Retrieving last MT5 error")
        return self.mt5.last_error()

    @_log_mt5_last_status_code
    def account_info(self) -> Any:
        """Get info on the current trading account.

        Returns:
            AccountInfo structure or None.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving account information.")
        response = self.mt5.account_info()
        self._validate_mt5_response_is_not_none(
            response=response, operation="account_info"
        )
        return response

    @_log_mt5_last_status_code
    def terminal_info(self) -> Any:
        """Get the connected MetaTrader 5 client terminal status and settings.

        Returns:
            TerminalInfo structure or None.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving terminal information.")
        response = self.mt5.terminal_info()
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="terminal_info",
        )
        return response

    @_log_mt5_last_status_code
    def symbols_total(self) -> int:
        """Get the number of all financial instruments in the terminal.

        Returns:
            Total number of symbols.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving total number of symbols.")
        return self.mt5.symbols_total()

    @_log_mt5_last_status_code
    def symbols_get(self, group: str | None = None) -> tuple[Any, ...]:
        """Get all financial instruments from the terminal.

        Args:
            group: Symbol group filter.

        Returns:
            Tuple of symbol info structures or None.
        """
        self._initialize_if_needed()
        if group is not None:
            self.logger.info("Retrieving symbols for group: %s", group)
            response = self.mt5.symbols_get(group=group)
            context = f"group={group}"
        else:
            self.logger.info("Retrieving all symbols.")
            response = self.mt5.symbols_get()
            context = None
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="symbols_get",
            context=context,
        )
        return response

    @_log_mt5_last_status_code
    def symbol_info(self, symbol: str) -> Any:
        """Get data on the specified financial instrument.

        Args:
            symbol: Symbol name.

        Returns:
            Symbol info structure or None.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving information for symbol: %s", symbol)
        response = self.mt5.symbol_info(symbol)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="symbol_info",
            context=f"symbol={symbol}",
        )
        return response

    @_log_mt5_last_status_code
    def symbol_info_tick(self, symbol: str) -> Any:
        """Get the last tick for the specified financial instrument.

        Args:
            symbol: Symbol name.

        Returns:
            Tick info structure or None.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving last tick for symbol: %s", symbol)
        response = self.mt5.symbol_info_tick(symbol)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="symbol_info_tick",
            context=f"symbol={symbol}",
        )
        return response

    @_log_mt5_last_status_code
    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Select a symbol in the MarketWatch window or remove a symbol from the window.

        Args:
            symbol: Symbol name.
            enable: True to show, False to hide.

        Returns:
            True if successful, False otherwise.
        """
        self._initialize_if_needed()
        self.logger.info("Selecting symbol: %s, enable=%s", symbol, enable)
        response = self.mt5.symbol_select(symbol, enable)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="symbol_select",
            context=f"symbol={symbol}, enable={enable}",
        )
        return response

    @_log_mt5_last_status_code
    def market_book_add(self, symbol: str) -> bool:
        """Subscribe the terminal to the Market Depth change events for a specified symbol.

        Args:
            symbol: Symbol name.

        Returns:
            True if successful, False otherwise.
        """  # noqa: E501
        self._initialize_if_needed()
        self.logger.info("Adding market book for symbol: %s", symbol)
        response = self.mt5.market_book_add(symbol)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="market_book_add",
            context=f"symbol={symbol}",
        )
        return response

    @_log_mt5_last_status_code
    def market_book_get(self, symbol: str) -> tuple[Any, ...]:
        """Return a tuple from BookInfo featuring Market Depth entries for the specified symbol.

        Args:
            symbol: Symbol name.

        Returns:
            Tuple of BookInfo structures or None.
        """  # noqa: E501
        self._initialize_if_needed()
        self.logger.info("Retrieving market book for symbol: %s", symbol)
        response = self.mt5.market_book_get(symbol)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="market_book_get",
            context=f"symbol={symbol}",
        )
        return response

    @_log_mt5_last_status_code
    def market_book_release(self, symbol: str) -> bool:
        """Cancels subscription of the terminal to the Market Depth change events for a specified symbol.

        Args:
            symbol: Symbol name.

        Returns:
            True if successful, False otherwise.
        """  # noqa: E501
        self._initialize_if_needed()
        self.logger.info("Releasing market book for symbol: %s", symbol)
        response = self.mt5.market_book_release(symbol)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="market_book_release",
            context=f"symbol={symbol}",
        )
        return response

    @_log_mt5_last_status_code
    def copy_rates_from(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime | int,
        count: int,
    ) -> Any:
        """Get bars from the terminal starting from the specified date.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            date_from: Start date or timestamp.
            count: Number of bars to retrieve.

        Returns:
            Array of rates or None.
        """
        self._initialize_if_needed()
        self.logger.info(
            "Copying rates from symbol: %s, timeframe: %d, date_from: %s, count: %d",
            symbol,
            timeframe,
            date_from,
            count,
        )
        response = self.mt5.copy_rates_from(symbol, timeframe, date_from, count)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="copy_rates_from",
            context=(
                f"symbol={symbol}, timeframe={timeframe},"
                f" date_from={date_from}, count={count}"
            ),
        )
        return response

    @_log_mt5_last_status_code
    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> Any:
        """Get bars from the terminal starting from the specified index.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            start_pos: Starting position.
            count: Number of bars to retrieve.

        Returns:
            Array of rates or None.
        """
        self._initialize_if_needed()
        self.logger.info(
            (
                "Copying rates from position:"
                " symbol=%s, timeframe=%d, start_pos=%d, count=%d"
            ),
            symbol,
            timeframe,
            start_pos,
            count,
        )
        response = self.mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="copy_rates_from_pos",
            context=(
                f"symbol={symbol}, timeframe={timeframe},"
                f" start_pos={start_pos}, count={count}"
            ),
        )
        return response

    @_log_mt5_last_status_code
    def copy_rates_range(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime | int,
        date_to: datetime | int,
    ) -> Any:
        """Get bars in the specified date range from the terminal.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            date_from: Start date or timestamp.
            date_to: End date or timestamp.

        Returns:
            Array of rates or None.
        """
        self._initialize_if_needed()
        self.logger.info(
            "Copying rates range: symbol=%s, timeframe=%d, date_from=%s, date_to=%s",
            symbol,
            timeframe,
            date_from,
            date_to,
        )
        response = self.mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="copy_rates_range",
            context=(
                f"symbol={symbol}, timeframe={timeframe},"
                f" date_from={date_from}, date_to={date_to}"
            ),
        )
        return response

    @_log_mt5_last_status_code
    def copy_ticks_from(
        self,
        symbol: str,
        date_from: datetime | int,
        count: int,
        flags: int,
    ) -> Any:
        """Get ticks from the terminal starting from the specified date.

        Args:
            symbol: Symbol name.
            date_from: Start date or timestamp.
            count: Number of ticks to retrieve.
            flags: Tick flags.

        Returns:
            Array of ticks or None.
        """
        self._initialize_if_needed()
        self.logger.info(
            "Copying ticks from symbol: %s, date_from: %s, count: %d, flags: %d",
            symbol,
            date_from,
            count,
            flags,
        )
        response = self.mt5.copy_ticks_from(symbol, date_from, count, flags)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="copy_ticks_from",
            context=(
                f"symbol={symbol}, date_from={date_from}, count={count}, flags={flags}"
            ),
        )
        return response

    @_log_mt5_last_status_code
    def copy_ticks_range(
        self,
        symbol: str,
        date_from: datetime | int,
        date_to: datetime | int,
        flags: int,
    ) -> Any:
        """Get ticks for the specified date range from the terminal.

        Args:
            symbol: Symbol name.
            date_from: Start date or timestamp.
            date_to: End date or timestamp.
            flags: Tick flags.

        Returns:
            Array of ticks or None.
        """
        self._initialize_if_needed()
        self.logger.info(
            "Copying ticks range: symbol=%s, date_from=%s, date_to=%s, flags=%d",
            symbol,
            date_from,
            date_to,
            flags,
        )
        response = self.mt5.copy_ticks_range(symbol, date_from, date_to, flags)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="copy_ticks_range",
            context=(
                f"symbol={symbol}, date_from={date_from},"
                f" date_to={date_to}, flags={flags}"
            ),
        )
        return response

    @_log_mt5_last_status_code
    def orders_total(self) -> int:
        """Get the number of active orders.

        Returns:
            Number of active orders.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving total number of active orders.")
        return self.mt5.orders_total()

    @_log_mt5_last_status_code
    def orders_get(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
    ) -> tuple[Any, ...]:
        """Get active orders with the ability to filter by symbol or ticket.

        Args:
            symbol: Symbol name filter.
            group: Group filter.
            ticket: Order ticket filter.

        Returns:
            Tuple of order info structures or None.
        """
        self._initialize_if_needed()
        if ticket is not None:
            self.logger.info("Retrieving order with ticket: %d", ticket)
            response = self.mt5.orders_get(ticket=ticket)
            context = f"ticket={ticket}"
        elif group is not None:
            self.logger.info("Retrieving orders for group: %s", group)
            response = self.mt5.orders_get(group=group)
            context = f"group={group}"
        elif symbol is not None:
            self.logger.info("Retrieving orders for symbol: %s", symbol)
            response = self.mt5.orders_get(symbol=symbol)
            context = f"symbol={symbol}"
        else:
            self.logger.info("Retrieving all active orders.")
            response = self.mt5.orders_get()
            context = None
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="orders_get",
            context=context,
        )
        return response

    @_log_mt5_last_status_code
    def order_calc_margin(
        self,
        action: int,
        symbol: str,
        volume: float,
        price: float,
    ) -> float:
        """Return margin in the account currency to perform a specified trading operation.

        Args:
            action: Order type (ORDER_TYPE_BUY or ORDER_TYPE_SELL).
            symbol: Symbol name.
            volume: Volume in lots.
            price: Open price.

        Returns:
            Required margin amount or None.
        """  # noqa: E501
        self._initialize_if_needed()
        self.logger.info(
            "Calculating margin: action=%d, symbol=%s, volume=%.2f, price=%.5f",
            action,
            symbol,
            volume,
            price,
        )
        response = self.mt5.order_calc_margin(action, symbol, volume, price)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="order_calc_margin",
            context=f"action={action}, symbol={symbol}, volume={volume}, price={price}",
        )
        return response

    @_log_mt5_last_status_code
    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float:
        """Return profit in the account currency for a specified trading operation.

        Args:
            action: Order type (ORDER_TYPE_BUY or ORDER_TYPE_SELL).
            symbol: Symbol name.
            volume: Volume in lots.
            price_open: Open price.
            price_close: Close price.

        Returns:
            Calculated profit or None.
        """
        self._initialize_if_needed()
        self.logger.info(
            (
                "Calculating profit: action=%d, symbol=%s, volume=%.2f,"
                " price_open=%.5f, price_close=%.5f"
            ),
            action,
            symbol,
            volume,
            price_open,
            price_close,
        )
        response = self.mt5.order_calc_profit(
            action, symbol, volume, price_open, price_close
        )
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="order_calc_profit",
            context=(
                f"action={action}, symbol={symbol}, volume={volume},"
                f" price_open={price_open}, price_close={price_close}"
            ),
        )
        return response

    @_log_mt5_last_status_code
    def order_check(self, request: dict[str, Any]) -> Any:
        """Check funds sufficiency for performing a required trading operation.

        Args:
            request: Trade request dictionary.

        Returns:
            OrderCheckResult structure or None.
        """
        self._initialize_if_needed()
        self.logger.info("Checking order with request: %s", request)
        response = self.mt5.order_check(request)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="order_check",
            context=f"request={request}",
        )
        return response

    @_log_mt5_last_status_code
    def order_send(self, request: dict[str, Any]) -> Any:
        """Send a request to perform a trading operation from the terminal to the trade server.

        Args:
            request: Trade request dictionary.

        Returns:
            OrderSendResult structure or None.
        """  # noqa: E501
        self._initialize_if_needed()
        self.logger.info("Sending order with request: %s", request)
        response = self.mt5.order_send(request)
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="order_send",
            context=f"request={request}",
        )
        return response

    @_log_mt5_last_status_code
    def positions_total(self) -> int:
        """Get the number of open positions.

        Returns:
            Number of open positions.
        """
        self._initialize_if_needed()
        self.logger.info("Retrieving total number of open positions.")
        return self.mt5.positions_total()

    @_log_mt5_last_status_code
    def positions_get(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
    ) -> tuple[Any, ...]:
        """Get open positions with the ability to filter by symbol or ticket.

        Args:
            symbol: Symbol name filter.
            group: Group filter.
            ticket: Position ticket filter.

        Returns:
            Tuple of position info structures or None.
        """
        self._initialize_if_needed()
        if ticket is not None:
            self.logger.info("Retrieving position with ticket: %d", ticket)
            response = self.mt5.positions_get(ticket=ticket)
            context = f"ticket={ticket}"
        elif group is not None:
            self.logger.info("Retrieving positions for group: %s", group)
            response = self.mt5.positions_get(group=group)
            context = f"group={group}"
        elif symbol is not None:
            self.logger.info("Retrieving positions for symbol: %s", symbol)
            response = self.mt5.positions_get(symbol=symbol)
            context = f"symbol={symbol}"
        else:
            self.logger.info("Retrieving all open positions.")
            response = self.mt5.positions_get()
            context = None
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="positions_get",
            context=context,
        )
        return response

    @_log_mt5_last_status_code
    def history_orders_total(
        self,
        date_from: datetime | int,
        date_to: datetime | int,
    ) -> int:
        """Get the number of orders in trading history within the specified interval.

        Args:
            date_from: Start date or timestamp.
            date_to: End date or timestamp.

        Returns:
            Number of historical orders.
        """
        self._initialize_if_needed()
        self.logger.info(
            "Retrieving total number of historical orders from %s to %s",
            date_from,
            date_to,
        )
        return self.mt5.history_orders_total(date_from, date_to)

    @_log_mt5_last_status_code
    def history_orders_get(
        self,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        group: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> tuple[Any, ...]:
        """Get orders from trading history with the ability to filter by ticket or position.

        Args:
            date_from: Start date or timestamp.
            date_to: End date or timestamp.
            group: Group filter.
            ticket: Order ticket filter.
            position: Position ticket filter.

        Returns:
            Tuple of historical order info structures or None.
        """  # noqa: E501
        self._initialize_if_needed()
        if ticket is not None:
            self.logger.info("Retrieving order with ticket: %d", ticket)
            response = self.mt5.history_orders_get(ticket=ticket)
            context = f"ticket={ticket}"
        elif position is not None:
            self.logger.info("Retrieving order for position: %d", position)
            response = self.mt5.history_orders_get(position=position)
            context = f"position={position}"
        elif group is not None:
            self.logger.info(
                "Retrieving orders for group: %s, date_from: %s, date_to: %s",
                group,
                date_from,
                date_to,
            )
            response = self.mt5.history_orders_get(date_from, date_to, group=group)
            context = f"date_from={date_from}, date_to={date_to}, group={group}"
        else:
            self.logger.info(
                "Retrieving all historical orders from %s to %s",
                date_from,
                date_to,
            )
            response = self.mt5.history_orders_get(date_from, date_to)
            context = f"date_from={date_from}, date_to={date_to}"
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="history_orders_get",
            context=context,
        )
        return response

    @_log_mt5_last_status_code
    def history_deals_total(
        self,
        date_from: datetime | int,
        date_to: datetime | int,
    ) -> int:
        """Get the number of deals in trading history within the specified interval.

        Args:
            date_from: Start date or timestamp.
            date_to: End date or timestamp.

        Returns:
            Number of historical deals.
        """
        self._initialize_if_needed()
        self.logger.info(
            "Retrieving total number of historical deals from %s to %s",
            date_from,
            date_to,
        )
        return self.mt5.history_deals_total(date_from, date_to)

    @_log_mt5_last_status_code
    def history_deals_get(
        self,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        group: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> tuple[Any, ...]:
        """Get deals from trading history within the specified interval with the ability to filter by ticket or position.

        Args:
            date_from: Start date or timestamp.
            date_to: End date or timestamp.
            group: Group filter.
            ticket: Order ticket filter.
            position: Position ticket filter.

        Returns:
            Tuple of historical deal info structures or None.
        """  # noqa: E501
        self._initialize_if_needed()
        if ticket is not None:
            self.logger.info("Retrieving deal with ticket: %d", ticket)
            response = self.mt5.history_deals_get(ticket=ticket)
            context = f"ticket={ticket}"
        elif position is not None:
            self.logger.info("Retrieving deal for position: %d", position)
            response = self.mt5.history_deals_get(position=position)
            context = f"position={position}"
        elif group is not None:
            self.logger.info(
                "Retrieving deals for group: %s, date_from: %s, date_to: %s",
                group,
                date_from,
                date_to,
            )
            response = self.mt5.history_deals_get(date_from, date_to, group=group)
            context = f"date_from={date_from}, date_to={date_to}, group={group}"
        else:
            self.logger.info(
                "Retrieving all historical deals from %s to %s",
                date_from,
                date_to,
            )
            response = self.mt5.history_deals_get(date_from, date_to)
            context = f"date_from={date_from}, date_to={date_to}"
        self._validate_mt5_response_is_not_none(
            response=response,
            operation="history_deals_get",
            context=context,
        )
        return response

    def _initialize_if_needed(self) -> None:
        """Ensure the MetaTrader5 client is initialized before performing operations."""
        if not self._is_initialized:
            self.initialize()

    def _validate_mt5_response_is_not_none(
        self,
        response: Any,
        operation: str,
        context: str | None = None,
    ) -> None:
        """Validate that the MetaTrader5 response is not None.

        Args:
            response: The response object to validate.
            operation: Name of the operation being validated.
            context: Additional context about the operation.

        Raises:
            Mt5RuntimeError: With error details from MetaTrader5.
        """
        if response is None:
            error_message = (
                f"MT5 {operation} returned {response}:"
                f" last_error={self.mt5.last_error()}"
            ) + (f" context={context}" if context else "")
            raise Mt5RuntimeError(error_message)
