"""Tests for API authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest
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


def test_version_endpoint_allows_requests_when_auth_disabled(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test protected endpoints work without API key when auth is disabled."""
    monkeypatch.delenv("MT5_API_KEY", raising=False)

    response = client.get("/api/v1/version")

    assert response.status_code == 200


def test_get_api_key_missing_env_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_api_key returns None when environment variable is missing."""
    from mt5api.auth import get_api_key  # noqa: PLC0415

    monkeypatch.delenv("MT5_API_KEY", raising=False)

    assert get_api_key() is None


def test_openapi_does_not_require_api_key_when_auth_disabled(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test OpenAPI omits API key security when auth is disabled."""
    monkeypatch.delenv("MT5_API_KEY", raising=False)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert "securitySchemes" not in schema.get("components", {})
    assert "security" not in schema["paths"]["/api/v1/version"]["get"]
