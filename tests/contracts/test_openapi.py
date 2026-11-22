"""Application-wide OpenAPI contract tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_docs_and_openapi_available(
    client: TestClient, api_headers: dict[str, str]
) -> None:
    """Docs and OpenAPI endpoints should be available."""
    for path in ("/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers=api_headers).status_code == 200

    docs_response = client.get("/docs", headers=api_headers)
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json", headers=api_headers)
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
