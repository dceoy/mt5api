"""Tests for FastAPI application helpers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI

from mt5api.constants import API_KEY_SECURITY_SCHEME_NAME

if TYPE_CHECKING:
    import pytest
    from pytest_mock import MockerFixture


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


def test_patch_validation_error_responses_updates_422_schema() -> None:
    """OpenAPI validation responses should advertise RFC 7807 Problem Details."""
    from mt5api import main  # noqa: PLC0415

    openapi_schema: dict[str, Any] = {
        "components": {
            "schemas": {
                "HTTPValidationError": {"type": "object"},
                "ValidationError": {"type": "object"},
            },
        },
        "paths": {
            "/rates/from": {
                "get": {
                    "responses": {
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": (
                                            "#/components/schemas/HTTPValidationError"
                                        ),
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }

    main._patch_validation_error_responses(openapi_schema)  # pyright: ignore[reportPrivateUsage]

    schemas = openapi_schema["components"]["schemas"]
    assert "ErrorResponse" in schemas
    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas
    assert openapi_schema["paths"]["/rates/from"]["get"]["responses"]["422"] == {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
            },
        },
    }


def test_release_market_book_subscriptions_clears_state(
    mocker: MockerFixture,
) -> None:
    """Shutdown cleanup should release tracked market-book subscriptions."""
    from mt5api import dependencies  # noqa: PLC0415

    test_app = FastAPI()
    test_app.state.active_market_book_subscriptions = {"GBPUSD", "EURUSD"}
    test_client = mocker.Mock()
    test_app.state.market_book_cleanup_client = test_client

    asyncio.run(dependencies.release_market_book_subscriptions(test_app))

    assert test_client.market_book_release.call_count == 2
    test_client.market_book_release.assert_any_call(symbol="EURUSD")
    test_client.market_book_release.assert_any_call(symbol="GBPUSD")
    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_handles_missing_client() -> None:
    """Shutdown cleanup should clear tracked state when no client is available."""
    from mt5api import dependencies  # noqa: PLC0415

    test_app = FastAPI()
    test_app.state.active_market_book_subscriptions = {"EURUSD"}
    test_app.state.market_book_cleanup_client = None

    asyncio.run(dependencies.release_market_book_subscriptions(test_app))

    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_skips_when_state_is_missing() -> None:
    """Shutdown cleanup should no-op when no subscriptions were ever tracked."""
    from mt5api import dependencies  # noqa: PLC0415

    test_app = FastAPI()

    asyncio.run(dependencies.release_market_book_subscriptions(test_app))

    assert not hasattr(test_app.state, "active_market_book_subscriptions")
    assert not hasattr(test_app.state, "market_book_cleanup_client")


def test_release_market_book_subscriptions_skips_when_state_is_empty(
    mocker: MockerFixture,
) -> None:
    """Shutdown cleanup should no-op when the tracked subscription set is empty."""
    from mt5api import dependencies  # noqa: PLC0415

    test_app = FastAPI()
    test_app.state.active_market_book_subscriptions = set()
    test_client = mocker.Mock()
    test_app.state.market_book_cleanup_client = test_client

    asyncio.run(dependencies.release_market_book_subscriptions(test_app))

    test_client.market_book_release.assert_not_called()
    assert test_app.state.market_book_cleanup_client is test_client


def test_release_market_book_subscriptions_continues_after_failure(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """Shutdown cleanup should continue releasing symbols after one failure."""
    from mt5api import dependencies  # noqa: PLC0415

    test_app = FastAPI()
    test_app.state.active_market_book_subscriptions = {"GBPUSD", "EURUSD"}
    test_client = mocker.Mock()
    test_client.market_book_release.side_effect = [RuntimeError("boom"), None]
    test_app.state.market_book_cleanup_client = test_client

    with caplog.at_level("ERROR"):
        asyncio.run(dependencies.release_market_book_subscriptions(test_app))

    assert test_client.market_book_release.call_count == 2
    test_client.market_book_release.assert_any_call(symbol="EURUSD")
    test_client.market_book_release.assert_any_call(symbol="GBPUSD")
    assert "Failed to release market book for" in caplog.text
    assert test_app.state.active_market_book_subscriptions == set()
    assert test_app.state.market_book_cleanup_client is None
