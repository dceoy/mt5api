"""Tests for application lifespan handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    import pytest


def test_lifespan_calls_shutdown_on_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test shutdown hook runs when TestClient context exits."""
    from pdmt5.api import main  # noqa: PLC0415

    shutdown_called = {"value": False}

    def fake_shutdown() -> None:
        shutdown_called["value"] = True

    monkeypatch.setattr(main, "shutdown_mt5_client", fake_shutdown)

    with TestClient(main.app) as client:
        response = client.get("/api/v1/health")
        status_code = response.status_code

    assert (status_code, shutdown_called["value"]) == (200, True)
