"""Tests for FastAPI application helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi.testclient import TestClient

from mt5api.constants import API_KEY_SECURITY_SCHEME_NAME

if TYPE_CHECKING:
    import pytest


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
    rate_content = openapi_schema["paths"]["/rates/from"]["get"]["responses"]["200"][
        "content"
    ]
    assert rate_content["application/parquet"]["schema"] == {
        "type": "string",
        "format": "binary",
    }
    health_content = openapi_schema["paths"]["/health"]["get"]["responses"]["200"][
        "content"
    ]
    assert "application/parquet" not in health_content


def test_openapi_helpers_ignore_malformed_dynamic_values() -> None:
    """OpenAPI patchers skip values with unexpected runtime shapes."""
    from mt5api import main  # noqa: PLC0415

    main._strip_auth_from_openapi(  # pyright: ignore[reportPrivateUsage]
        {"components": [], "paths": []}
    )
    main._strip_auth_from_openapi(  # pyright: ignore[reportPrivateUsage]
        {"components": {"securitySchemes": []}, "paths": {}}
    )
    main._patch_validation_error_responses(  # pyright: ignore[reportPrivateUsage]
        {"components": [], "paths": {}},
    )
    main._patch_validation_error_responses(  # pyright: ignore[reportPrivateUsage]
        {"components": {"schemas": []}, "paths": {}},
    )

    malformed_schema: dict[str, Any] = {
        "paths": {
            "/bad-methods": [],
            "/bad-operation": {"get": []},
            "/missing-responses": {
                "get": {"parameters": [{"in": "query", "name": "format"}]},
            },
            "/bad-parameters": {
                "get": {
                    "parameters": "invalid",
                    "responses": {},
                },
            },
            "/bad-responses": {
                "get": {
                    "parameters": [{"in": "query", "name": "format"}],
                    "responses": [],
                },
            },
            "/bad-success": {
                "get": {
                    "parameters": [{"in": "query", "name": "format"}],
                    "responses": {"200": []},
                },
            },
            "/bad-content": {
                "get": {
                    "parameters": [{"in": "query", "name": "format"}],
                    "responses": {"200": {"content": []}},
                },
            },
        }
    }
    main._patch_parquet_success_responses(  # pyright: ignore[reportPrivateUsage]
        malformed_schema
    )


def test_lifespan_calls_shutdown_on_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The application shutdown hook runs when TestClient context exits."""
    from mt5api import main  # noqa: PLC0415

    shutdown_called = {"value": False}

    def fake_shutdown(_state: object) -> None:
        shutdown_called["value"] = True

    monkeypatch.setattr(main, "shutdown_mt5_client", fake_shutdown)

    with TestClient(main.app) as client:
        response = client.get("/health")
        status_code = response.status_code

    assert (status_code, shutdown_called["value"]) == (200, True)
