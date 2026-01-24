"""Service wrapper around the pdmt5 dependency."""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any, Callable


class Pdmt5Service:
    """Thin wrapper to interact with pdmt5 in a REST-friendly way."""

    def __init__(self) -> None:
        self._module = importlib.import_module("pdmt5")
        self._api = self._resolve_api()

    def _resolve_api(self) -> Any:
        if hasattr(self._module, "Pdmt5"):
            return self._module.Pdmt5()
        if hasattr(self._module, "MetaTrader5"):
            return self._module.MetaTrader5
        return self._module

    def _get_callable(self, name: str) -> Callable[..., Any] | None:
        return getattr(self._api, name, None)

    def call_any(self, *names: str, **kwargs: Any) -> Any:
        for name in names:
            func = self._get_callable(name)
            if func:
                return func(**kwargs)
        raise RuntimeError(f"pdmt5 does not expose callable {names!r}")

    def initialize(self, payload: dict[str, Any]) -> Any:
        return self.call_any("initialize", "init", **payload)

    def shutdown(self) -> Any:
        return self.call_any("shutdown", "close")

    def account_info(self) -> Any:
        return self.call_any("account_info", "get_account")

    def symbols(self) -> Any:
        return self.call_any("symbols_get", "symbols")

    def symbol_info(self, symbol: str) -> Any:
        return self.call_any("symbol_info", "get_symbol", symbol=symbol)

    def positions(self) -> Any:
        return self.call_any("positions_get", "positions")

    def orders(self) -> Any:
        return self.call_any("orders_get", "orders")

    def order_send(self, request: dict[str, Any]) -> Any:
        return self.call_any("order_send", "send_order", request=request)


@lru_cache
def get_service() -> Pdmt5Service:
    return Pdmt5Service()


def configure_service(config: dict[str, Any]) -> None:
    service = get_service()
    service.initialize(config)
