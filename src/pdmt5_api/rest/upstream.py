"""Helpers to load upstream REST API modules from the pdmt5 dependency."""

from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable

_UPSTREAM_MODULES = (
    "pdmt5.rest.app",
    "pdmt5.rest.api",
    "pdmt5.api.rest.app",
)


def _load_upstream_module() -> Any | None:
    for module_name in _UPSTREAM_MODULES:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
    return None


def _call_create_app(
    create_app: Callable[..., Any], config: dict[str, Any] | None
) -> Any:
    if config is None:
        return create_app()
    signature = inspect.signature(create_app)
    if "config" in signature.parameters:
        return create_app(config=config)
    if any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    ):
        return create_app(config=config)
    return create_app()


def load_upstream_app(config: dict[str, Any] | None = None) -> Any | None:
    module = _load_upstream_module()
    if not module:
        return None
    if hasattr(module, "create_app"):
        return _call_create_app(module.create_app, config)
    if hasattr(module, "app"):
        return module.app
    return None
