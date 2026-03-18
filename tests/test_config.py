"""Tests for API configuration helpers."""

from __future__ import annotations

import importlib

import pytest

from mt5api.constants import (
    DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    ENV_MT5API_ROUTER_PREFIX,
    ENV_MT5API_SECRET_KEY,
)


@pytest.mark.parametrize(
    ("raw_prefix", "expected_prefix"),
    [
        (None, ""),
        ("", ""),
        ("   ", ""),
        ("/", ""),
        ("api/v1", "/api/v1"),
        ("/api/v1", "/api/v1"),
        ("/api/v1/", "/api/v1"),
        (" /api/v1/ ", "/api/v1"),
    ],
)
def test_normalize_api_router_prefix(
    raw_prefix: str | None,
    expected_prefix: str,
) -> None:
    """Router prefix should be normalized for FastAPI mounting."""
    from mt5api import config  # noqa: PLC0415

    assert config.normalize_api_router_prefix(raw_prefix) == expected_prefix


@pytest.mark.parametrize(
    "raw_prefix", ["api//v1", "api?v=1", "../admin", "../../admin"]
)
def test_normalize_api_router_prefix_rejects_invalid_values(raw_prefix: str) -> None:
    """Router prefix should reject malformed or unsafe path values."""
    from mt5api import config  # noqa: PLC0415

    with pytest.raises(ValueError, match="Invalid MT5API_ROUTER_PREFIX"):
        config.normalize_api_router_prefix(raw_prefix)


@pytest.mark.parametrize(
    ("raw_secret_key", "expected_secret_key"),
    [
        (None, None),
        ("", None),
        ("secret-key", "secret-key"),
    ],
)
def test_get_configured_mt5api_secret_key(
    monkeypatch: pytest.MonkeyPatch,
    raw_secret_key: str | None,
    expected_secret_key: str | None,
) -> None:
    """MT5 API secret key config should treat empty strings as disabled auth."""
    from mt5api import config  # noqa: PLC0415

    if raw_secret_key is None:
        monkeypatch.delenv(ENV_MT5API_SECRET_KEY, raising=False)
    else:
        monkeypatch.setenv(ENV_MT5API_SECRET_KEY, raw_secret_key)

    assert config.get_configured_mt5api_secret_key() == expected_secret_key


@pytest.mark.parametrize(
    ("raw_limit", "expected_limit"),
    [
        (None, DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS),
        ("1", 1),
        ("250", 250),
    ],
)
def test_get_configured_max_market_book_subscriptions(
    monkeypatch: pytest.MonkeyPatch,
    raw_limit: str | None,
    expected_limit: int,
) -> None:
    """Market-book subscription limit should read a positive configured integer."""
    from mt5api import config  # noqa: PLC0415

    if raw_limit is None:
        monkeypatch.delenv(ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS, raising=False)
    else:
        monkeypatch.setenv(ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS, raw_limit)

    assert config.get_configured_max_market_book_subscriptions() == expected_limit


@pytest.mark.parametrize("raw_limit", ["0", "-1", "not-a-number"])
def test_get_configured_max_market_book_subscriptions_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    raw_limit: str,
) -> None:
    """Market-book subscription limit should reject invalid values."""
    from mt5api import config  # noqa: PLC0415

    monkeypatch.setenv(ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS, raw_limit)

    with pytest.raises(
        ValueError,
        match="Invalid MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS",
    ):
        config.get_configured_max_market_book_subscriptions()


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
