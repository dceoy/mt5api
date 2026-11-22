"""Application-wide OpenAPI contract tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mt5api.main import app

if TYPE_CHECKING:
    import pytest


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


def test_mounted_docs_follow_emitted_urls(
    api_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mounted documentation and its schema use the mount for every URL."""
    parent = FastAPI()
    parent.mount("/mt5", app)
    with TestClient(parent, base_url="http://localhost") as mounted:
        docs = mounted.get("/mt5/docs", headers=api_headers).text
        schema_url = re.search(r"url: '([^']+)'", docs)
        redirect_url = re.search(
            r"oauth2RedirectUrl: window.location.origin \+ '([^']+)'", docs
        )
        assert schema_url
        assert redirect_url
        assert schema_url.group(1) == "/mt5/openapi.json"
        assert redirect_url.group(1) == "/mt5/docs/oauth2-redirect"
        schema = mounted.get(schema_url.group(1), headers=api_headers).json()
        assert schema["servers"][0]["url"] == "/mt5"
        assert (
            mounted.get(redirect_url.group(1), headers=api_headers).status_code == 200
        )
        redoc = mounted.get("/mt5/redoc", headers=api_headers).text
        redoc_url = re.search(r'spec-url="([^"]+)"', redoc)
        assert redoc_url
        assert redoc_url.group(1) == schema_url.group(1)
        assert mounted.get(redoc_url.group(1), headers=api_headers).status_code == 200

        monkeypatch.setattr(
            app, "openapi_schema", {**app.openapi(), "servers": [{"url": "/mt5"}]}
        )
        assert mounted.get(schema_url.group(1), headers=api_headers).json()[
            "servers"
        ] == [{"url": "/mt5"}]
        monkeypatch.setattr(app, "root_path_in_servers", False)
        monkeypatch.setattr(
            app, "openapi_schema", {**app.openapi(), "servers": [{"url": "/other"}]}
        )
        assert mounted.get(schema_url.group(1), headers=api_headers).json()[
            "servers"
        ] == [{"url": "/other"}]
