"""Tests for FastAPI application helpers."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import Mock

from fastapi import FastAPI

from mt5api.constants import API_KEY_SECURITY_SCHEME_NAME


def test_strip_auth_from_openapi_handles_non_dict_components() -> None:
    """OpenAPI auth stripping should tolerate missing component mappings."""
    from mt5api import main  # noqa: PLC0415

    openapi_schema: dict[str, Any] = {
        "security": [{API_KEY_SECURITY_SCHEME_NAME: []}],
        "components": None,
        "paths": {
            "/bad": [],
            "/version": {
                "summary": "Version endpoint",
                "get": {"security": [{API_KEY_SECURITY_SCHEME_NAME: []}]},
            },
        },
    }

    main._strip_auth_from_openapi(openapi_schema)  # pyright: ignore[reportPrivateUsage]

    assert "security" not in openapi_schema
    assert "security" not in openapi_schema["paths"]["/version"]["get"]


def test_strip_auth_from_openapi_handles_non_dict_security_schemes() -> None:
    """OpenAPI auth stripping should tolerate non-dict security schemes."""
    from mt5api import main  # noqa: PLC0415

    openapi_schema: dict[str, Any] = {
        "components": {"securitySchemes": []},
        "paths": {},
    }

    main._strip_auth_from_openapi(openapi_schema)  # pyright: ignore[reportPrivateUsage]

    assert openapi_schema["components"]["securitySchemes"] == []


def test_strip_auth_from_openapi_preserves_other_security_schemes() -> None:
    """OpenAPI auth stripping should keep unrelated security schemes."""
    from mt5api import main  # noqa: PLC0415

    openapi_schema: dict[str, Any] = {
        "components": {
            "securitySchemes": {API_KEY_SECURITY_SCHEME_NAME: {}, "Other": {}}
        },
        "paths": {},
    }

    main._strip_auth_from_openapi(openapi_schema)  # pyright: ignore[reportPrivateUsage]

    assert openapi_schema["components"]["securitySchemes"] == {"Other": {}}


def test_release_market_book_subscriptions_clears_state() -> None:
    """Shutdown cleanup should release tracked market-book subscriptions."""
    from mt5api import main  # noqa: PLC0415

    test_app = FastAPI()
    test_app.state.active_market_book_subscriptions = {"GBPUSD", "EURUSD"}
    test_client = Mock()
    test_app.state.market_book_cleanup_client = test_client

    asyncio.run(
        main._release_market_book_subscriptions(test_app)  # pyright: ignore[reportPrivateUsage]
    )

    assert test_client.market_book_release.call_count == 2
    test_client.market_book_release.assert_any_call(symbol="EURUSD")
    test_client.market_book_release.assert_any_call(symbol="GBPUSD")
    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_handles_missing_client() -> None:
    """Shutdown cleanup should clear tracked state when no client is available."""
    from mt5api import main  # noqa: PLC0415

    test_app = FastAPI()
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.market_book_cleanup_client = None

    asyncio.run(
        main._release_market_book_subscriptions(test_app)  # pyright: ignore[reportPrivateUsage]
    )

    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None
