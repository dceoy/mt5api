"""Tests for API configuration helpers."""

from __future__ import annotations

import importlib

import pytest

from mt5api.constants import (
    ENV_API_CORS_ORIGINS,
    ENV_API_RATE_LIMIT,
    ENV_API_ROUTER_PREFIX,
)


def test_get_cors_origins_parses_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """CORS origins should split on commas and trim whitespace."""
    monkeypatch.setenv(ENV_API_CORS_ORIGINS, "https://a.example, https://b.example")

    from mt5api import main  # noqa: PLC0415

    assert main._get_cors_origins() == [  # pyright: ignore[reportPrivateUsage]
        "https://a.example",
        "https://b.example",
    ]


def test_build_default_rate_limit_handles_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid rate limit values should default to 100/minute."""
    monkeypatch.setenv(ENV_API_RATE_LIMIT, "not-a-number")

    from mt5api import middleware  # noqa: PLC0415

    assert (
        middleware._build_default_rate_limit()  # pyright: ignore[reportPrivateUsage]
        == "100/minute"
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


def test_app_uses_api_router_prefix_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """App routes should be mounted under the configured API prefix."""
    monkeypatch.setenv(ENV_API_ROUTER_PREFIX, "api/v1")

    from mt5api import main  # noqa: PLC0415

    reloaded_main = importlib.reload(main)

    try:
        paths = reloaded_main.app.openapi()["paths"]

        assert "/api/v1/health" in paths
        assert "/api/v1/symbols" in paths
        assert "/health" not in paths
        assert "/symbols" not in paths
    finally:
        monkeypatch.delenv(ENV_API_ROUTER_PREFIX, raising=False)
        importlib.reload(main)
