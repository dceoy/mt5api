"""Contract tests for account and terminal endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unittest.mock import Mock

    from fastapi.testclient import TestClient


def test_get_account_info_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/account returns account info."""
    response = client.get("/api/v1/account", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["login"] == 12345

    mock_mt5_client.account_info_as_df.assert_called_with()


def test_get_terminal_info_returns_json(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/terminal returns terminal info."""
    response = client.get("/api/v1/terminal", headers=api_headers)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 1
    assert payload["data"][0]["connected"] is True

    mock_mt5_client.terminal_info_as_df.assert_called_with()


def test_get_account_info_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/account supports Parquet output."""
    response = client.get(
        "/api/v1/account?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.account_info_as_df.assert_called_with()


def test_get_terminal_info_returns_parquet(
    client: TestClient,
    api_headers: dict[str, str],
    mock_mt5_client: Mock,
) -> None:
    """GET /api/v1/terminal supports Parquet output."""
    response = client.get(
        "/api/v1/terminal?format=parquet",
        headers=api_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/parquet")

    mock_mt5_client.terminal_info_as_df.assert_called_with()
