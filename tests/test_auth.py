"""Tests for API authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.monkeypatch import MonkeyPatch
    from fastapi.testclient import TestClient


def test_version_endpoint_requires_authentication(client: TestClient) -> None:
    """Test version endpoint requires API key."""
    # No API key header
    response = client.get("/api/v1/version")

    assert response.status_code == 401

    data = response.json()["detail"]
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Required"
    assert "Missing API key" in data["detail"]


def test_version_endpoint_rejects_invalid_api_key(client: TestClient) -> None:
    """Test version endpoint rejects invalid API key."""
    headers = {"X-API-Key": "wrong-key"}
    response = client.get("/api/v1/version", headers=headers)

    assert response.status_code == 401

    data = response.json()["detail"]
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Failed"
    assert "Invalid API key" in data["detail"]


def test_version_endpoint_accepts_valid_api_key(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Test version endpoint accepts valid API key."""
    response = client.get("/api/v1/version", headers=api_headers)

    assert response.status_code == 200


def test_symbols_endpoint_requires_authentication(
    client: TestClient,
    mock_mt5_client: Mock,
) -> None:
    """Test router-level protected endpoints require API key."""
    response = client.get("/api/v1/symbols?group=*USD*")

    assert response.status_code == 401
    mock_mt5_client.symbols_get_as_df.assert_not_called()

    data = response.json()["detail"]
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Required"
    assert "Missing API key" in data["detail"]


def test_symbols_endpoint_rejects_invalid_api_key(
    client: TestClient,
    mock_mt5_client: Mock,
) -> None:
    """Test symbols endpoint rejects invalid API key."""
    headers = {"X-API-Key": "wrong-key"}
    response = client.get("/api/v1/symbols?group=*USD*", headers=headers)

    assert response.status_code == 401
    mock_mt5_client.symbols_get_as_df.assert_not_called()

    data = response.json()["detail"]
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Failed"
    assert "Invalid API key" in data["detail"]


def test_version_endpoint_allows_requests_when_auth_disabled(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test protected endpoints work without API key when auth is disabled."""
    from mt5api import auth  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)

    response = client.get("/api/v1/version")

    assert response.status_code == 200


def test_symbols_endpoint_allows_requests_when_auth_disabled(
    client: TestClient,
    mock_mt5_client: Mock,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test router-level protected endpoints work without API key."""
    from mt5api import auth  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)

    response = client.get("/api/v1/symbols?group=*USD*")

    assert response.status_code == 200
    mock_mt5_client.symbols_get_as_df.assert_called_with(group="*USD*")


def test_get_api_key_returns_none_when_auth_is_disabled(
    monkeypatch: MonkeyPatch,
) -> None:
    """Test get_api_key returns None when authentication is disabled."""
    from mt5api import auth  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)

    assert auth.get_api_key() is None


def test_openapi_does_not_require_api_key_when_auth_disabled(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test OpenAPI omits API key security when auth is disabled."""
    from mt5api import auth, main  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)
    monkeypatch.setattr(main.app, "openapi_schema", None)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert "securitySchemes" not in schema.get("components", {})
    assert "security" not in schema["paths"]["/api/v1/version"]["get"]
    assert "security" not in schema["paths"]["/api/v1/symbols"]["get"]
