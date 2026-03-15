"""Tests for FastAPI application helpers."""

from __future__ import annotations

from typing import Any

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
