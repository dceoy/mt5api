"""Tests for FastAPI application helpers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from mt5api.constants import API_KEY_SECURITY_SCHEME_NAME
from mt5api.dependencies import Mt5RuntimeState, release_market_book_subscriptions

if TYPE_CHECKING:
    import pytest
    from pytest_mock import MockerFixture


def test_strip_auth_from_openapi_preserves_other_security_schemes() -> None:
    """OpenAPI auth stripping keeps unrelated security schemes."""
    from mt5api import main  # noqa: PLC0415

    openapi_schema: dict[str, Any] = {
        "components": {
            "securitySchemes": {API_KEY_SECURITY_SCHEME_NAME: {}, "Other": {}}
        },
        "paths": {
            "/rates/from": {
                "parameters": [{"name": "symbol", "in": "query"}],
                "get": {"security": [{API_KEY_SECURITY_SCHEME_NAME: []}]},
            },
        },
    }
    main._strip_auth_from_openapi(openapi_schema)  # pyright: ignore[reportPrivateUsage]
    assert openapi_schema["components"]["securitySchemes"] == {"Other": {}}
    assert "security" not in openapi_schema["paths"]["/rates/from"]["get"]


def test_patch_validation_error_responses_updates_422_schema() -> None:
    """OpenAPI validation responses advertise RFC 7807 Problem Details."""
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
                    "responses": {"422": {"description": "Validation Error"}},
                },
            },
        },
    }
    main._patch_validation_error_responses(openapi_schema)  # pyright: ignore[reportPrivateUsage]
    schemas = openapi_schema["components"]["schemas"]
    assert "ErrorResponse" in schemas
    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas
    response = openapi_schema["paths"]["/rates/from"]["get"]["responses"]["422"]
    assert response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }


def test_patch_parquet_success_responses_only_updates_formatted_operations() -> None:
    """OpenAPI advertises Parquet only for operations with the format query."""
    from mt5api import main  # noqa: PLC0415

    openapi_schema: dict[str, Any] = {
        "paths": {
            "/rates/from": {
                "get": {
                    "parameters": [{"name": "format", "in": "query"}],
                    "responses": {
                        "200": {
                            "content": {"application/json": {"schema": {}}},
                        }
                    },
                }
            },
            "/health": {
                "get": {
                    "parameters": [],
                    "responses": {
                        "200": {
                            "content": {"application/json": {"schema": {}}},
                        }
                    },
                }
            },
        }
    }
    main._patch_parquet_success_responses(openapi_schema)  # pyright: ignore[reportPrivateUsage]
    rate_content = openapi_schema["paths"]["/rates/from"]["get"]["responses"]["200"]["content"]
    assert rate_content["application/parquet"]["schema"] == {
        "type": "string",
        "format": "binary",
    }
    health_content = openapi_schema["paths"]["/health"]["get"]["responses"]["200"]["content"]
    assert "application/parquet" not in health_content


def test_release_market_book_subscriptions_clears_runtime_state(
    mocker: MockerFixture,
) -> None:
    """Shutdown cleanup releases tracked subscriptions and ownership."""
    cleanup_client = mocker.Mock()
    state = Mt5RuntimeState(
        market_book_subscriptions={"GBPUSD", "EURUSD"},
        market_book_cleanup_client=cleanup_client,
    )
    asyncio.run(release_market_book_subscriptions(state))
    cleanup_client.market_book_release.assert_any_call(symbol="EURUSD")
    cleanup_client.market_book_release.assert_any_call(symbol="GBPUSD")
    assert cleanup_client.market_book_release.call_count == 2
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_handles_missing_client() -> None:
    """Cleanup clears tracking even when no release client is available."""
    state = Mt5RuntimeState(market_book_subscriptions={"EURUSD"})
    asyncio.run(release_market_book_subscriptions(state))
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_skips_empty_state(
    mocker: MockerFixture,
) -> None:
    """Cleanup does not call a client when no subscriptions are active."""
    cleanup_client = mocker.Mock()
    state = Mt5RuntimeState(market_book_cleanup_client=cleanup_client)
    asyncio.run(release_market_book_subscriptions(state))
    cleanup_client.market_book_release.assert_not_called()
    assert state.market_book_cleanup_client is None


def test_release_market_book_subscriptions_continues_after_failure(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """Cleanup continues after a release failure."""
    cleanup_client = mocker.Mock()
    cleanup_client.market_book_release.side_effect = [RuntimeError("boom"), None]
    state = Mt5RuntimeState(
        market_book_subscriptions={"GBPUSD", "EURUSD"},
        market_book_cleanup_client=cleanup_client,
    )
    with caplog.at_level("ERROR"):
        asyncio.run(release_market_book_subscriptions(state))
    assert cleanup_client.market_book_release.call_count == 2
    assert "Failed to release market book for" in caplog.text
    assert state.market_book_subscriptions == set()
    assert state.market_book_cleanup_client is None
