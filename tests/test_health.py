"""Tests for health check endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mt5api.constants import API_VERSION

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


def test_health_endpoint_returns_healthy_status(client: TestClient) -> None:
    """Test health endpoint returns healthy status when MT5 is connected."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["mt5_connected"] is True
    assert data["mt5_version"] == "5.0.4321"
    assert data["api_version"] == API_VERSION


def test_health_endpoint_no_authentication_required(client: TestClient) -> None:
    """Test health endpoint works without authentication."""
    # No X-API-Key header
    response = client.get("/health")

    assert response.status_code == 200


def test_version_endpoint_returns_mt5_version(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Test version endpoint returns MT5 version info."""
    response = client.get("/version", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["format"] == "json"
    assert payload["count"] == 1

    data = payload["data"]
    assert data["version"] == "5.0.4321"
    assert data["build"] == 4321
    assert "release_date" in data


def test_version_endpoint_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
) -> None:
    """Test version endpoint returns Parquet when requested."""
    headers = {**api_headers, "Accept": "application/parquet"}
    response = client.get("/version", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")


def test_docs_and_openapi_available(client: TestClient) -> None:
    """Docs and OpenAPI endpoints should be available."""
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    assert "paths" in openapi_response.json()


def test_last_error_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /last-error returns last MT5 error info."""
    response = client.get("/last-error", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"]["error_code"] == 1
    assert payload["data"]["error_description"] == "Success"

    mock_mt5_client.last_error_as_dict.assert_called_with()


def test_last_error_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /last-error supports Parquet output."""
    response = client.get("/last-error?format=parquet", headers=api_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.last_error_as_dict.assert_called_with()


@pytest.mark.asyncio
async def test_get_health_handles_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_health handles MT5 runtime errors gracefully."""
    from mt5api.routers import health  # noqa: PLC0415

    def raise_runtime_error() -> None:
        error_message = "MT5 unavailable"
        raise RuntimeError(error_message)

    monkeypatch.setattr(health, "get_mt5_client", raise_runtime_error)

    response = await health.get_health()

    assert response.mt5_connected is False


@pytest.mark.asyncio
async def test_get_health_handles_empty_version_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_health handles empty version info."""
    from mt5api.routers import health  # noqa: PLC0415

    class DummyClient:
        def version_as_dict(self) -> dict[str, str]:
            return {}

    def get_client() -> DummyClient:
        return DummyClient()

    monkeypatch.setattr(health, "get_mt5_client", get_client)

    response = await health.get_health()

    assert response.mt5_version is None
