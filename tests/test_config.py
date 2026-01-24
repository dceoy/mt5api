"""Tests for API configuration helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def test_get_cors_origins_parses_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """CORS origins should split on commas and trim whitespace."""
    monkeypatch.setenv("API_CORS_ORIGINS", "https://a.example, https://b.example")

    from pdmt5.api import main  # noqa: PLC0415

    assert main._get_cors_origins() == [  # pyright: ignore[reportPrivateUsage]
        "https://a.example",
        "https://b.example",
    ]


def test_build_default_rate_limit_handles_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid rate limit values should default to 100/minute."""
    monkeypatch.setenv("API_RATE_LIMIT", "not-a-number")

    from pdmt5.api import middleware  # noqa: PLC0415

    assert (
        middleware._build_default_rate_limit()  # pyright: ignore[reportPrivateUsage]
        == "100/minute"
    )
