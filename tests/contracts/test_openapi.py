"""Application-wide OpenAPI contract tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch
    from fastapi.testclient import TestClient


def test_docs_and_openapi_available(client: TestClient) -> None:
    """Docs and OpenAPI endpoints should be available."""
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi = openapi_response.json()
    assert "paths" in openapi
    assert "ErrorResponse" in openapi["components"]["schemas"]
    assert "HTTPValidationError" not in openapi["components"]["schemas"]
    assert openapi["paths"]["/rates/from"]["get"]["responses"]["422"] == {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
            },
        },
    }


def test_openapi_does_not_require_api_key_when_auth_disabled(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    """OpenAPI omits API-key security when authentication is disabled."""
    from mt5api import auth, main  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)
    monkeypatch.setattr(main.app, "openapi_schema", None)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert "securitySchemes" not in schema.get("components", {})
    assert "security" not in schema["paths"]["/version"]["get"]
    assert "security" not in schema["paths"]["/symbols"]["get"]
