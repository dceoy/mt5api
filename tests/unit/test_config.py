"""Tests for API configuration helpers."""

from __future__ import annotations

import pytest

from mt5api.constants import (
    DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    ENV_MT5API_LOG_LEVEL,
    ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    ENV_MT5API_MT5_PATH,
    ENV_MT5API_PORT,
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
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    assert config.normalize_api_router_prefix(raw_prefix) == expected_prefix


@pytest.mark.parametrize(
    "raw_prefix", ["api//v1", "api?v=1", "../admin", "../../admin"]
)
def test_normalize_api_router_prefix_rejects_invalid_values(raw_prefix: str) -> None:
    """Router prefix should reject malformed or unsafe path values."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    with pytest.raises(ValueError, match="Invalid MT5API_ROUTER_PREFIX"):
        config.normalize_api_router_prefix(raw_prefix)


@pytest.mark.parametrize("raw_path", [None, "", r"C:\Program Files\MT5\terminal64.exe"])
def test_get_configured_mt5_path(
    monkeypatch: pytest.MonkeyPatch, raw_path: str | None
) -> None:
    """The terminal path is optional and otherwise preserved verbatim."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    if raw_path is None:
        monkeypatch.delenv(ENV_MT5API_MT5_PATH, raising=False)
    else:
        monkeypatch.setenv(ENV_MT5API_MT5_PATH, raw_path)
    assert config.get_configured_mt5_path() == (raw_path or None)


@pytest.mark.parametrize("raw", [None, "", "  "])
def test_get_configured_mt5_terminals_empty(monkeypatch: pytest.MonkeyPatch, raw: str | None) -> None:
    """Unset and blank terminal mappings are empty."""
    from mt5api.config import get_configured_mt5_terminals  # ruff: ignore[import-outside-top-level]

    if raw is None:
        monkeypatch.delenv("MT5API_MT5_TERMINALS", raising=False)
    else:
        monkeypatch.setenv("MT5API_MT5_TERMINALS", raw)
    assert get_configured_mt5_terminals() == {}


def test_get_configured_mt5_terminals(monkeypatch: pytest.MonkeyPatch) -> None:
    """Names and paths are trimmed."""
    from mt5api.config import get_configured_mt5_terminals  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv("MT5API_MT5_TERMINALS", r" index = C:\index.exe , commodity = C:\commodity.exe ")
    assert get_configured_mt5_terminals() == {"index": r"C:\index.exe", "commodity": r"C:\commodity.exe"}


@pytest.mark.parametrize("raw", ["a", "=path", "name=", "a=x,", "a=x,a=y"])
def test_get_configured_mt5_terminals_rejects_invalid(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """Malformed or duplicate entries are rejected."""
    from mt5api.config import get_configured_mt5_terminals  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv("MT5API_MT5_TERMINALS", raw)
    with pytest.raises(ValueError, match="Invalid MT5API_MT5_TERMINALS"):
        get_configured_mt5_terminals()


@pytest.mark.parametrize(
    ("raw_secret_key", "expected_secret_key"),
    [
        (None, None),
        ("   ", None),
        (" key ", " key "),
        ("", None),
        ("secret-key", "secret-key"),
    ],
)
def test_get_configured_mt5api_secret_key(
    monkeypatch: pytest.MonkeyPatch,
    raw_secret_key: str | None,
    expected_secret_key: str | None,
) -> None:
    """MT5 API secret key config should treat blank keys as missing."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    if raw_secret_key is None:
        monkeypatch.delenv(ENV_MT5API_SECRET_KEY, raising=False)
    else:
        monkeypatch.setenv(ENV_MT5API_SECRET_KEY, raw_secret_key)

    assert config.get_configured_mt5api_secret_key() == expected_secret_key


@pytest.mark.parametrize(
    ("raw_port", "expected_port"),
    [
        (None, 8000),
        ("1", 1),
        ("65535", 65535),
    ],
)
def test_get_configured_api_port(
    monkeypatch: pytest.MonkeyPatch,
    raw_port: str | None,
    expected_port: int,
) -> None:
    """API port config should read a valid TCP port."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    if raw_port is None:
        monkeypatch.delenv(ENV_MT5API_PORT, raising=False)
    else:
        monkeypatch.setenv(ENV_MT5API_PORT, raw_port)

    assert config.get_configured_api_port() == expected_port


@pytest.mark.parametrize("raw_port", ["0", "65536", "not-a-number"])
def test_get_configured_api_port_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    raw_port: str,
) -> None:
    """API port config should reject invalid values."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv(ENV_MT5API_PORT, raw_port)

    with pytest.raises(ValueError, match="Invalid MT5API_PORT"):
        config.get_configured_api_port()


@pytest.mark.parametrize(
    ("raw_log_level", "expected_log_level", "expected_python_log_level"),
    [
        (None, "info", "INFO"),
        ("WARNING", "warning", "WARNING"),
        ("trace", "trace", "DEBUG"),
    ],
)
def test_get_configured_api_log_level(
    monkeypatch: pytest.MonkeyPatch,
    raw_log_level: str | None,
    expected_log_level: str,
    expected_python_log_level: str,
) -> None:
    """API log-level config should support uvicorn levels."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    if raw_log_level is None:
        monkeypatch.delenv(ENV_MT5API_LOG_LEVEL, raising=False)
    else:
        monkeypatch.setenv(ENV_MT5API_LOG_LEVEL, raw_log_level)

    assert config.get_configured_api_log_level() == expected_log_level
    assert config.get_configured_python_log_level() == expected_python_log_level


def test_get_configured_api_log_level_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API log-level config should reject unsupported values."""
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv(ENV_MT5API_LOG_LEVEL, "verbose")

    with pytest.raises(ValueError, match="Invalid MT5API_LOG_LEVEL"):
        config.get_configured_api_log_level()


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
    from mt5api import config  # ruff: ignore[import-outside-top-level]

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
    from mt5api import config  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv(ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS, raw_limit)

    with pytest.raises(
        ValueError,
        match="Invalid MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS",
    ):
        config.get_configured_max_market_book_subscriptions()


def test_trusted_hosts_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow explicit comma-separated host names."""
    from mt5api.config import get_configured_trusted_hosts  # ruff: ignore[import-outside-top-level]

    monkeypatch.delenv("MT5API_TRUSTED_HOSTS", raising=False)
    assert get_configured_trusted_hosts() == [
        "localhost",
        "127.0.0.1",
        "[::1]",
    ]
    monkeypatch.setenv("MT5API_TRUSTED_HOSTS", "example.com, localhost, ")
    assert get_configured_trusted_hosts() == ["example.com", "localhost"]


@pytest.mark.parametrize("raw", ["", "  , ", "*", "localhost,*,"])
def test_trusted_hosts_rejects_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    """Empty allowlists and universal wildcards fail configuration."""
    from mt5api.config import get_configured_trusted_hosts  # ruff: ignore[import-outside-top-level]

    monkeypatch.setenv("MT5API_TRUSTED_HOSTS", raw)
    with pytest.raises(ValueError, match="Invalid MT5API_TRUSTED_HOSTS"):
        get_configured_trusted_hosts()
