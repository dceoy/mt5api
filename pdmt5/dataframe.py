"""MetaTrader5 data client with pandas DataFrame conversion."""

from __future__ import annotations

import time
from datetime import datetime  # noqa: TC003
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from .mt5 import Mt5Client, Mt5RuntimeError
from .utils import (
    detect_and_convert_time_to_datetime,
    set_index_if_possible,
)


class Mt5Config(BaseModel):
    """Configuration for MetaTrader5 connection."""

    model_config = ConfigDict(frozen=True)
    path: str | None = Field(
        default=None, description="Path to MetaTrader5 terminal EXE file"
    )
    login: int | None = Field(default=None, description="Trading account login")
    password: str | None = Field(default=None, description="Trading account password")
    server: str | None = Field(default=None, description="Trading server name")
    timeout: int | None = Field(
        default=None, description="Connection timeout in milliseconds"
    )


class Mt5DataClient(Mt5Client):
    """MetaTrader5 data client with pandas DataFrame and dictionary conversion.

    This class provides a pandas-friendly interface to MetaTrader5 functions,
    converting native MetaTrader5 data structures to pandas DataFrames with pydantic
    validation.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: Mt5Config = Field(
        default_factory=Mt5Config,
        description="MetaTrader5 connection configuration",
    )
    retry_count: int = Field(
        default=3,
        ge=0,
        description="Number of retry attempts for connection initialization",
    )

    def initialize_and_login_mt5(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize MetaTrader5 connection with retry logic.

        This method overrides the base class to add retry logic and use config values.

        Args:
            path: Path to terminal EXE file (overrides config).
            login: Account login (overrides config).
            password: Account password (overrides config).
            server: Server name (overrides config).
            timeout: Connection timeout (overrides config).

        Raises:
            Mt5RuntimeError: If initialization fails after retries.
        """
        path = path or self.config.path
        login_kwargs = {
            "login": login or self.config.login,
            "password": password or self.config.password,
            "server": server or self.config.server,
            "timeout": timeout or self.config.timeout,
        }
        for i in range(1 + max(0, self.retry_count)):
            if i:
                self.logger.warning(
                    "Retrying MT5 initialization (%d/%d)...",
                    i,
                    self.retry_count,
                )
                time.sleep(i)
            if self.initialize(path=path, **login_kwargs) and (
                (not login_kwargs["login"]) or self.login(**login_kwargs)
            ):
                return
        error_message = (
            f"MT5 initialize and login failed after {self.retry_count} retries:"
            f" {self.last_error()}"
        )
        raise Mt5RuntimeError(error_message)

    def version_as_dict(self) -> dict[str, int | str]:
        """Return MetaTrader5 version information as a dictionary.

        Returns:
            Dictionary with MetaTrader5 version information.
        """
        response = self.version()
        return {
            "mt5_terminal_version": response[0],
            "build": response[1],
            "build_release_date": response[2],
        }

    @set_index_if_possible(index_parameters="index_keys")
    def version_as_df(self, index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG002
        """Return MetaTrader5 version information as a data frame.

        Args:
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with MetaTrader5 version information.
        """
        return pd.DataFrame([self.version_as_dict()])

    def last_error_as_dict(self) -> dict[str, Any]:
        """Get the last error information as a dictionary.

        Returns:
            Dictionary with last error information.
        """
        response = self.last_error()
        return {"error_code": response[0], "error_description": response[1]}

    @set_index_if_possible(index_parameters="index_keys")
    def last_error_as_df(self, index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG002
        """Get the last error information as a data frame.

        Args:
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with last error information.
        """
        return pd.DataFrame([self.last_error_as_dict()])

    def account_info_as_dict(self) -> dict[str, Any]:
        """Get info on the current account as a dictionary.

        Returns:
            Dictionary with account information.
        """
        return self.account_info()._asdict()

    @set_index_if_possible(index_parameters="index_keys")
    def account_info_as_df(self, index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG002
        """Get info on the current account as a data frame.

        Args:
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with account information.
        """
        return pd.DataFrame([self.account_info_as_dict()])

    def terminal_info_as_dict(self) -> dict[str, Any]:
        """Get the connected terminal status and settings as a dictionary.

        Returns:
            Dictionary with terminal information.
        """
        return self.terminal_info()._asdict()

    @set_index_if_possible(index_parameters="index_keys")
    def terminal_info_as_df(self, index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG002
        """Get the connected terminal status and settings as a data frame.

        Args:
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with terminal information.
        """
        return pd.DataFrame([self.terminal_info_as_dict()])

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def symbols_get_as_dicts(
        self,
        group: str | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get symbols as a list of dictionaries.

        Args:
            group: Symbol group filter (e.g., "*USD*", "Forex*").
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with symbol information.
        """
        return [s._asdict() for s in self.symbols_get(group=group)]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def symbols_get_as_df(
        self,
        group: str | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get symbols as a data frame.

        Args:
            group: Symbol group filter (e.g., "*USD*", "Forex*").
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with symbol information.
        """
        return pd.DataFrame(
            self.symbols_get_as_dicts(group=group, skip_to_datetime=True)
        )

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def symbol_info_as_dict(
        self,
        symbol: str,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get data on a specific symbol as a dictionary.

        Args:
            symbol: Symbol name.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            Dictionary with symbol information.
        """
        return self.symbol_info(symbol=symbol)._asdict()

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def symbol_info_as_df(
        self,
        symbol: str,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get data on a specific symbol as a data frame.

        Args:
            symbol: Symbol name.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with symbol information.
        """
        return pd.DataFrame([
            self.symbol_info_as_dict(symbol=symbol, skip_to_datetime=True)
        ])

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def symbol_info_tick_as_dict(
        self,
        symbol: str,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get the last tick for the specified financial instrument as a dictionary.

        Args:
            symbol: Symbol name.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            Dictionary with tick information.
        """
        return self.symbol_info_tick(symbol=symbol)._asdict()

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def symbol_info_tick_as_df(
        self,
        symbol: str,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get the last tick for the specified financial instrument as a data frame.

        Args:
            symbol: Symbol name.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with tick information.
        """
        return pd.DataFrame([
            self.symbol_info_tick_as_dict(symbol=symbol, skip_to_datetime=True)
        ])

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def market_book_get_as_dicts(
        self,
        symbol: str,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get market depth for a specified symbol as a list of dictionaries.

        Args:
            symbol: Symbol name.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with market depth data.
        """
        return [b._asdict() for b in self.market_book_get(symbol=symbol)]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def market_book_get_as_df(
        self,
        symbol: str,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get market depth for a specified symbol as a data frame.

        Args:
            symbol: Symbol name.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with market depth data.
        """
        return pd.DataFrame(
            self.market_book_get_as_dicts(symbol=symbol, skip_to_datetime=True)
        )

    def copy_rates_from_as_dicts(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime,
        count: int,
        skip_to_datetime: bool = False,
    ) -> list[dict[str, Any]]:
        """Get bars for a specified date range as a list of dictionaries.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            date_from: Start date.
            count: Number of rates to retrieve.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with OHLCV data.
        """
        return self.copy_rates_from_as_df(
            symbol=symbol,
            timeframe=timeframe,
            date_from=date_from,
            count=count,
            skip_to_datetime=skip_to_datetime,
            index_keys=None,
        ).to_dict(orient="records")

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def copy_rates_from_as_df(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime,
        count: int,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get bars for a specified date range as a data frame.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            date_from: Start date.
            count: Number of rates to retrieve.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with OHLCV data.
        """
        self._validate_positive_count(count=count)
        return pd.DataFrame(
            self.copy_rates_from(
                symbol=symbol,
                timeframe=timeframe,
                date_from=date_from,
                count=count,
            )
        )

    def copy_rates_from_pos_as_dicts(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
        skip_to_datetime: bool = False,
    ) -> list[dict[str, Any]]:
        """Get bars from a specified position as a list of dictionaries.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            start_pos: Start position.
            count: Number of rates to retrieve.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with OHLCV data.
        """
        return self.copy_rates_from_pos_as_df(
            symbol=symbol,
            timeframe=timeframe,
            start_pos=start_pos,
            count=count,
            skip_to_datetime=skip_to_datetime,
            index_keys=None,
        ).to_dict(orient="records")

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def copy_rates_from_pos_as_df(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get bars from a specified position as a data frame.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            start_pos: Start position.
            count: Number of rates to retrieve.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with OHLCV data.
        """
        self._validate_positive_count(count=count)
        self._validate_non_negative_position(position=start_pos)
        return pd.DataFrame(
            self.copy_rates_from_pos(
                symbol=symbol,
                timeframe=timeframe,
                start_pos=start_pos,
                count=count,
            )
        )

    def copy_rates_range_as_dicts(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime,
        date_to: datetime,
        skip_to_datetime: bool = False,
    ) -> list[dict[str, Any]]:
        """Get bars for a specified date range as a list of dictionaries.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            date_from: Start date.
            date_to: End date.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with OHLCV data.
        """
        return self.copy_rates_range_as_df(
            symbol=symbol,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to,
            skip_to_datetime=skip_to_datetime,
            index_keys=None,
        ).to_dict(orient="records")

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def copy_rates_range_as_df(
        self,
        symbol: str,
        timeframe: int,
        date_from: datetime,
        date_to: datetime,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get bars for a specified date range as a data frame.

        Args:
            symbol: Symbol name.
            timeframe: Timeframe constant.
            date_from: Start date.
            date_to: End date.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with OHLCV data.
        """
        self._validate_date_range(date_from=date_from, date_to=date_to)
        return pd.DataFrame(
            self.copy_rates_range(
                symbol=symbol,
                timeframe=timeframe,
                date_from=date_from,
                date_to=date_to,
            )
        )

    def copy_ticks_from_as_dicts(
        self,
        symbol: str,
        date_from: datetime,
        count: int,
        flags: int,
        skip_to_datetime: bool = False,
    ) -> list[dict[str, Any]]:
        """Get ticks from a specified date as a list of dictionaries.

        Args:
            symbol: Symbol name.
            date_from: Start date.
            count: Number of ticks to retrieve.
            flags: Tick flags (use constants from MetaTrader5).
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with tick data.
        """
        return self.copy_ticks_from_as_df(
            symbol=symbol,
            date_from=date_from,
            count=count,
            flags=flags,
            skip_to_datetime=skip_to_datetime,
            index_keys=None,
        ).to_dict(orient="records")  # type: ignore[reportReturnType]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def copy_ticks_from_as_df(
        self,
        symbol: str,
        date_from: datetime,
        count: int,
        flags: int,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get ticks from a specified date as a data frame.

        Args:
            symbol: Symbol name.
            date_from: Start date.
            count: Number of ticks to retrieve.
            flags: Tick flags (use constants from MetaTrader5).
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with tick data.
        """
        self._validate_positive_count(count=count)
        return pd.DataFrame(
            self.copy_ticks_from(
                symbol=symbol,
                date_from=date_from,
                count=count,
                flags=flags,
            )
        )

    def copy_ticks_range_as_dicts(
        self,
        symbol: str,
        date_from: datetime,
        date_to: datetime,
        flags: int,
        skip_to_datetime: bool = False,
    ) -> list[dict[str, Any]]:
        """Get ticks for a specified date range as a list of dictionaries.

        Args:
            symbol: Symbol name.
            date_from: Start date.
            date_to: End date.
            flags: Tick flags (use constants from MetaTrader5).
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with tick data.
        """
        return self.copy_ticks_range_as_df(
            symbol=symbol,
            date_from=date_from,
            date_to=date_to,
            flags=flags,
            skip_to_datetime=skip_to_datetime,
            index_keys=None,
        ).to_dict(orient="records")  # type: ignore[reportReturnType]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def copy_ticks_range_as_df(
        self,
        symbol: str,
        date_from: datetime,
        date_to: datetime,
        flags: int,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get ticks for a specified date range as a data frame.

        Args:
            symbol: Symbol name.
            date_from: Start date.
            date_to: End date.
            flags: Tick flags (use constants from MetaTrader5).
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with tick data.
        """
        self._validate_date_range(date_from=date_from, date_to=date_to)
        return pd.DataFrame(
            self.copy_ticks_range(
                symbol=symbol,
                date_from=date_from,
                date_to=date_to,
                flags=flags,
            )
        )

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def orders_get_as_dicts(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get active orders with optional filters as a list of dictionaries.

        Args:
            symbol: Optional symbol filter.
            group: Optional group filter.
            ticket: Optional order ticket filter.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with order information or empty list if no orders.
        """
        return [
            o._asdict()
            for o in self.orders_get(symbol=symbol, group=group, ticket=ticket)
        ]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def orders_get_as_df(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get active orders with optional filters as a data frame.

        Args:
            symbol: Optional symbol filter.
            group: Optional group filter.
            ticket: Optional order ticket filter.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with order information or empty DataFrame if no orders.
        """
        return pd.DataFrame(
            self.orders_get_as_dicts(
                symbol=symbol,
                group=group,
                ticket=ticket,
                skip_to_datetime=True,
            )
        )

    def order_check_as_dict(self, request: dict[str, Any]) -> dict[str, Any]:
        """Check funds sufficiency for performing a requested trading operation as a dictionary.

        Args:
            request: Order request parameters.

        Returns:
            Dictionary with order check results.
        """  # noqa: E501
        return {
            k: (v._asdict() if k == "request" else v)
            for k, v in self.order_check(request=request)._asdict().items()
        }

    @set_index_if_possible(index_parameters="index_keys")
    def order_check_as_df(
        self,
        request: dict[str, Any],
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Check funds sufficiency for performing a requested trading operation as a data frame.

        Args:
            request: Order request parameters.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with order check results.
        """  # noqa: E501
        return pd.DataFrame([
            self._flatten_dict_to_one_level(
                dictionary=self.order_check_as_dict(request=request),
            )
        ])

    def order_send_as_dict(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a request to perform a trading operation from the terminal to the trade server as a dictionary.

        Args:
            request: Order request parameters.

        Returns:
            Dictionary with order send results.
        """  # noqa: E501
        return {
            k: (v._asdict() if k == "request" else v)
            for k, v in self.order_send(request=request)._asdict().items()
        }

    @set_index_if_possible(index_parameters="index_keys")
    def order_send_as_df(
        self,
        request: dict[str, Any],
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Send a request to perform a trading operation from the terminal to the trade server as a data frame.

        Args:
            request: Order request parameters.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with order send results.
        """  # noqa: E501
        return pd.DataFrame([
            self._flatten_dict_to_one_level(
                dictionary=self.order_send_as_dict(request=request),
            )
        ])

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def positions_get_as_dicts(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get open positions with optional filters as a list of dictionaries.

        Args:
            symbol: Optional symbol filter.
            group: Optional group filter.
            ticket: Optional position ticket filter.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with position information or empty list if no
            positions.
        """
        return [
            p._asdict()
            for p in self.positions_get(symbol=symbol, group=group, ticket=ticket)
        ]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def positions_get_as_df(
        self,
        symbol: str | None = None,
        group: str | None = None,
        ticket: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get open positions with optional filters as a data frame.

        Args:
            symbol: Optional symbol filter.
            group: Optional group filter.
            ticket: Optional position ticket filter.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with position information or empty DataFrame if no positions.
        """
        return pd.DataFrame(
            self.positions_get_as_dicts(
                symbol=symbol,
                group=group,
                ticket=ticket,
                skip_to_datetime=True,
            )
        )

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def history_orders_get_as_dicts(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        group: str | None = None,
        symbol: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get historical orders with optional filters as a list of dictionaries.

        Args:
            date_from: Start date (required if not using ticket/position).
            date_to: End date (required if not using ticket/position).
            group: Optional group filter.
            symbol: Optional symbol filter.
            ticket: Get orders by ticket.
            position: Get orders by position.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with historical order information.
        """
        self._validate_history_input(
            date_from=date_from,
            date_to=date_to,
            ticket=ticket,
            position=position,
        )
        return [
            o._asdict()
            for o in self.history_orders_get(
                date_from=date_from,
                date_to=date_to,
                group=(f"*{symbol}*" if symbol else group),
                ticket=ticket,
                position=position,
            )
        ]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def history_orders_get_as_df(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        group: str | None = None,
        symbol: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get historical orders with optional filters as a data frame.

        Args:
            date_from: Start date (required if not using ticket/position).
            date_to: End date (required if not using ticket/position).
            group: Optional group filter.
            symbol: Optional symbol filter.
            ticket: Get orders by ticket.
            position: Get orders by position.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with historical order information.
        """
        return pd.DataFrame(
            self.history_orders_get_as_dicts(
                date_from=date_from,
                date_to=date_to,
                group=group,
                symbol=symbol,
                ticket=ticket,
                position=position,
                skip_to_datetime=True,
            )
        )

    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def history_deals_get_as_dicts(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        group: str | None = None,
        symbol: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get historical deals with optional filters as a list of dictionaries.

        Args:
            date_from: Start date (required if not using ticket/position).
            date_to: End date (required if not using ticket/position).
            group: Optional group filter.
            symbol: Optional symbol filter.
            ticket: Get deals by order ticket.
            position: Get deals by position ticket.
            skip_to_datetime: Whether to skip converting time to datetime.

        Returns:
            List of dictionaries with historical deal information.
        """
        self._validate_history_input(
            date_from=date_from,
            date_to=date_to,
            ticket=ticket,
            position=position,
        )
        return [
            d._asdict()
            for d in self.history_deals_get(
                date_from=date_from,
                date_to=date_to,
                group=(f"*{symbol}*" if symbol else group),
                ticket=ticket,
                position=position,
            )
        ]

    @set_index_if_possible(index_parameters="index_keys")
    @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
    def history_deals_get_as_df(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        group: str | None = None,
        symbol: str | None = None,
        ticket: int | None = None,
        position: int | None = None,
        skip_to_datetime: bool = False,  # noqa: ARG002
        index_keys: str | None = None,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get historical deals with optional filters as a data frame.

        Args:
            date_from: Start date (required if not using ticket/position).
            date_to: End date (required if not using ticket/position).
            group: Optional group filter.
            symbol: Optional symbol filter.
            ticket: Get deals by order ticket.
            position: Get deals by position ticket.
            skip_to_datetime: Whether to skip converting time to datetime.
            index_keys: Column name to set as index if provided.

        Returns:
            DataFrame with historical deal information.
        """
        return pd.DataFrame(
            self.history_deals_get_as_dicts(
                date_from=date_from,
                date_to=date_to,
                group=group,
                symbol=symbol,
                ticket=ticket,
                position=position,
                skip_to_datetime=True,
            )
        )

    def _validate_history_input(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        ticket: int | None = None,
        position: int | None = None,
    ) -> None:
        """Validate input parameters for history retrieval methods.

        Args:
            date_from: Start date.
            date_to: End date.
            ticket: Order ticket.
            position: Position ticket.

        Raises:
            ValueError: If both date_from and date_to are not provided
                when not using ticket or position.
        """
        if ticket is not None or position is not None:
            pass
        elif date_from is None or date_to is None:
            error_message = (
                "Both date_from and date_to must be provided"
                " if not using ticket or position."
            )
            raise ValueError(error_message)
        else:
            self._validate_date_range(date_from=date_from, date_to=date_to)

    @staticmethod
    def _validate_positive_count(count: int) -> None:
        """Validate that count is positive.

        Args:
            count: Count value to validate.

        Raises:
            ValueError: If count is not positive.
        """
        if count <= 0:
            error_message = f"Invalid count: {count}. Count must be positive."
            raise ValueError(error_message)

    @staticmethod
    def _validate_date_range(date_from: datetime, date_to: datetime) -> None:
        """Validate that date_from is before date_to.

        Args:
            date_from: Start date.
            date_to: End date.

        Raises:
            ValueError: If date_from is not before date_to.
        """
        if date_from >= date_to:
            error_message = (
                f"Invalid date range: from={date_from} must be before to={date_to}"
            )
            raise ValueError(error_message)

    @staticmethod
    def _validate_positive_value(value: float, name: str) -> None:
        """Validate that a value is positive.

        Args:
            value: Value to validate.
            name: Name of the value for error message.

        Raises:
            ValueError: If value is not positive.
        """
        if value <= 0:
            if name.startswith("price_"):
                display_name = "Price"
            else:
                display_name = name.replace("_", " ").capitalize()
            error_message = f"Invalid {name}: {value}. {display_name} must be positive."
            raise ValueError(error_message)

    @staticmethod
    def _validate_non_negative_position(position: int) -> None:
        """Validate that position is non-negative.

        Args:
            position: Position value to validate.

        Raises:
            ValueError: If position is negative.
        """
        if position < 0:
            error_message = (
                f"Invalid start_pos: {position}. Position must be non-negative."
            )
            raise ValueError(error_message)

    @staticmethod
    def _flatten_dict_to_one_level(
        dictionary: dict[str, Any],
        sep: str = "_",
    ) -> dict[str, Any]:
        """Flatten a dictionary to one level with nested keys.

        Args:
            dictionary: Dictionary to flatten.
            sep: Separator for nested keys.

        Returns:
            Flattened dictionary.
        """
        items = []
        for k, v in dictionary.items():
            if isinstance(v, dict):
                items.extend((f"{k}{sep}{sk}", sv) for sk, sv in v.items())
            else:
                items.append((k, v))
        return dict(items)
