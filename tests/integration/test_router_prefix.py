"""Integration tests for application configuration and router mounting."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from mt5api.constants import ENV_MT5API_ROUTER_PREFIX

if TYPE_CHECKING:
    import pytest


def test_app_uses_api_router_prefix_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """App routes should be mounted under the configured API prefix."""
    monkeypatch.setenv(ENV_MT5API_ROUTER_PREFIX, "api/v1")

    from mt5api import main  # noqa: PLC0415

    reloaded_main = importlib.reload(main)

    try:
        paths = reloaded_main.app.openapi()["paths"]

        assert "/api/v1/health" in paths
        assert "/api/v1/symbols" in paths
        assert "/health" not in paths
        assert "/symbols" not in paths
    finally:
        monkeypatch.delenv(ENV_MT5API_ROUTER_PREFIX, raising=False)
        importlib.reload(main)
