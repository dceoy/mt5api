"""Tests for API authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from mt5api.constants import API_KEY_HEADER_NAME

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.monkeypatch import MonkeyPatch
    from fastapi.testclient import TestClient


def test_version_endpoint_requires_authentication(client: TestClient) -> None:
    """Test version endpoint requires API key."""
    # No API key header
    response = client.get("/version")

    assert response.status_code == 401

    data = response.json()
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Required"
    assert "Missing API key" in data["detail"]


def test_version_endpoint_rejects_invalid_api_key(client: TestClient) -> None:
    """Test version endpoint rejects invalid API key."""
    headers = {API_KEY_HEADER_NAME: "wrong-key"}
    response = client.get("/version", headers=headers)

    assert response.status_code == 401

    data = response.json()
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Failed"
    assert "Invalid API key" in data["detail"]


def test_symbols_endpoint_requires_authentication(
    client: TestClient,
    mock_mt5_client: Mock,
) -> None:
    """Test router-level protected endpoints require API key."""
    response = client.get("/symbols?group=*USD*")

    assert response.status_code == 401
    mock_mt5_client.symbols_get_as_df.assert_not_called()

    data = response.json()
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Required"
    assert "Missing API key" in data["detail"]


def test_symbols_endpoint_rejects_invalid_api_key(
    client: TestClient,
    mock_mt5_client: Mock,
) -> None:
    """Test symbols endpoint rejects invalid API key."""
    headers = {API_KEY_HEADER_NAME: "wrong-key"}
    response = client.get("/symbols?group=*USD*", headers=headers)

    assert response.status_code == 401
    mock_mt5_client.symbols_get_as_df.assert_not_called()

    data = response.json()
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Failed"
    assert "Invalid API key" in data["detail"]


@pytest.mark.parametrize(
    ("path", "request_kwargs", "mock_attr"),
    [
        (
            "/order/check",
            {
                "json": {
                    "request": {
                        "action": 1,
                        "symbol": "EURUSD",
                        "volume": 0.1,
                        "type": 0,
                        "price": 1.08500,
                    }
                }
            },
            "order_check_as_dict",
        ),
        ("/symbols/EURUSD/select", {}, "symbol_select"),
        ("/market-book/EURUSD/subscribe", {}, "market_book_add"),
        ("/market-book/EURUSD/unsubscribe", {}, "market_book_release"),
    ],
)
def test_trading_endpoints_require_authentication(
    client: TestClient,
    mock_mt5_client: Mock,
    path: str,
    request_kwargs: dict[str, Any],
    mock_attr: str,
) -> None:
    """Trading endpoints should reject unauthenticated requests."""
    response = client.post(path, **request_kwargs)

    assert response.status_code == 401
    getattr(mock_mt5_client, mock_attr).assert_not_called()

    data = response.json()
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Authentication Required"
    assert "Missing API key" in data["detail"]


def test_version_endpoint_allows_requests_when_auth_disabled(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test protected endpoints work without API key when auth is disabled."""
    from mt5api import auth  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)

    response = client.get("/version")

    assert response.status_code == 200


def test_symbols_endpoint_allows_requests_when_auth_disabled(
    client: TestClient,
    mock_mt5_client: Mock,
    monkeypatch: MonkeyPatch,
) -> None:
    """Test router-level protected endpoints work without API key."""
    from mt5api import auth  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)

    response = client.get("/symbols?group=*USD*")

    assert response.status_code == 200
    mock_mt5_client.symbols_get_as_df.assert_called_with(group="*USD*")


def test_get_api_key_returns_none_when_auth_is_disabled(
    monkeypatch: MonkeyPatch,
) -> None:
    """Test get_api_key returns None when authentication is disabled."""
    from mt5api import auth  # noqa: PLC0415

    monkeypatch.setattr(auth, "_API_KEY", None)

    assert auth.get_api_key() is None
