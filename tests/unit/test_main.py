"""Tests for FastAPI application helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from fastapi import FastAPI

from mt5api.dependencies import Mt5RuntimeState


def test_patch_validation_error_responses_updates_422_schema() -> None:
    """OpenAPI validation responses advertise RFC 7807 Problem Details."""
    from mt5api import main  # ruff: ignore[import-outside-top-level]

    openapi_schema: dict[str, Any] = {
        "components": {
            "schemas": {
                "HTTPValidationError": {"type": "object"},
                "ValidationError": {"type": "object"},
            },
        },
        "paths": {
            "/rates/from": {
                "get": {
                    "responses": {"422": {"description": "Validation Error"}},
                },
            },
        },
    }
    main._patch_validation_error_responses(openapi_schema)  # pyright: ignore[reportPrivateUsage]
    schemas = openapi_schema["components"]["schemas"]
    assert "ErrorResponse" in schemas
    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas
    response = openapi_schema["paths"]["/rates/from"]["get"]["responses"]["422"]
    assert response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }


def test_patch_parquet_success_responses_only_updates_formatted_operations() -> None:
    """OpenAPI advertises Parquet only for operations with the format query."""
    from mt5api import main  # ruff: ignore[import-outside-top-level]

    openapi_schema: dict[str, Any] = {
        "paths": {
            "/rates/from": {
                "get": {
                    "parameters": [{"name": "format", "in": "query"}],
                    "responses": {
                        "200": {
                            "content": {"application/json": {"schema": {}}},
                        }
                    },
                }
            },
            "/health": {
                "get": {
                    "parameters": [],
                    "responses": {
                        "200": {
                            "content": {"application/json": {"schema": {}}},
                        }
                    },
                }
            },
        }
    }
    main._patch_parquet_success_responses(openapi_schema)  # pyright: ignore[reportPrivateUsage]
    rate_content = openapi_schema["paths"]["/rates/from"]["get"]["responses"]["200"][
        "content"
    ]
    assert rate_content["application/parquet"]["schema"] == {
        "type": "string",
        "format": "binary",
    }
    health_content = openapi_schema["paths"]["/health"]["get"]["responses"]["200"][
        "content"
    ]
    assert "application/parquet" not in health_content


def test_openapi_helpers_ignore_malformed_dynamic_values() -> None:
    """OpenAPI patchers skip values with unexpected runtime shapes."""
    from mt5api import main  # ruff: ignore[import-outside-top-level]

    main._patch_validation_error_responses(  # pyright: ignore[reportPrivateUsage]
        {"components": [], "paths": {}},
    )
    main._patch_validation_error_responses(  # pyright: ignore[reportPrivateUsage]
        {"components": {"schemas": []}, "paths": {}},
    )

    assert list(main._iter_openapi_operations({"paths": []})) == []  # pyright: ignore[reportPrivateUsage]

    malformed_schema: dict[str, Any] = {
        "paths": {
            "/bad-methods": [],
            "/bad-operation": {"get": []},
            "/missing-responses": {
                "get": {"parameters": [{"in": "query", "name": "format"}]},
            },
            "/bad-parameters": {
                "get": {
                    "parameters": "invalid",
                    "responses": {},
                },
            },
            "/bad-responses": {
                "get": {
                    "parameters": [{"in": "query", "name": "format"}],
                    "responses": [],
                },
            },
            "/bad-success": {
                "get": {
                    "parameters": [{"in": "query", "name": "format"}],
                    "responses": {"200": []},
                },
            },
            "/bad-content": {
                "get": {
                    "parameters": [{"in": "query", "name": "format"}],
                    "responses": {"200": {"content": []}},
                },
            },
        }
    }
    main._patch_parquet_success_responses(  # pyright: ignore[reportPrivateUsage]
        malformed_schema
    )


def test_lifespan_calls_shutdown_on_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The application shutdown hook runs when TestClient context exits."""
    from mt5api import main  # ruff: ignore[import-outside-top-level]

    shutdown_called = {"value": False}

    def fake_shutdown(_state: object) -> None:
        shutdown_called["value"] = True

    monkeypatch.setattr(main, "shutdown_mt5_client", fake_shutdown)

    with TestClient(main.app, base_url="http://localhost") as client:
        response = client.get("/health")
        status_code = response.status_code

    assert (status_code, shutdown_called["value"]) == (200, True)


@pytest.mark.asyncio
async def test_lifespan_calls_shutdown_when_exception_is_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The application shutdown hook runs when its lifespan exits by error."""
    from mt5api import main  # ruff: ignore[import-outside-top-level]

    state = Mt5RuntimeState()
    shutdown_states: list[Mt5RuntimeState] = []

    def fake_initialize(
        _app: FastAPI,
        *,
        max_market_book_subscriptions: int | None = None,
    ) -> Mt5RuntimeState:
        _ = max_market_book_subscriptions
        return state

    def fake_shutdown(runtime_state: Mt5RuntimeState) -> None:
        shutdown_states.append(runtime_state)

    monkeypatch.setattr(main, "initialize_mt5_runtime_state", fake_initialize)
    release = AsyncMock()
    monkeypatch.setattr(main, "release_market_book_subscriptions", release)
    monkeypatch.setattr(main, "shutdown_mt5_client", fake_shutdown)

    message = "body failed"
    with pytest.raises(RuntimeError, match=message):
        async with main.lifespan(main.app):
            raise RuntimeError(message)

    release_call = release.await_args
    assert release_call is not None
    assert shutdown_states == [release_call.args[0]]


def test_startup_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The service cannot start with an unset or empty secret."""
    from mt5api import auth, main  # ruff: ignore[import-outside-top-level]

    monkeypatch.setattr(auth, "_API_KEY", None)
    with (
        pytest.raises(RuntimeError, match="MT5API_SECRET_KEY is required"),
        TestClient(main.app),
    ):
        pass


def test_trusted_hosts(client: TestClient) -> None:
    """Allow local hosts and reject arbitrary Host headers."""
    assert client.get("/health", headers={"host": "localhost:8000"}).status_code == 200
    assert client.get("/health", headers={"host": "127.0.0.1:8000"}).status_code == 200
    assert client.get("/health", headers={"host": "[::1]:8000"}).status_code == 200
    assert client.get("/health", headers={"host": "evil.example"}).status_code == 400


def test_fresh_app_import_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh import fails even when lifespan is never entered."""
    import importlib  # ruff: ignore[import-outside-top-level]
    import sys  # ruff: ignore[import-outside-top-level]

    from mt5api import auth  # ruff: ignore[import-outside-top-level]

    monkeypatch.delenv("MT5API_SECRET_KEY", raising=False)
    monkeypatch.setattr(auth, "_API_KEY", None)
    monkeypatch.delitem(sys.modules, "mt5api.main", raising=False)
    with pytest.raises(RuntimeError, match="MT5API_SECRET_KEY is required"):
        importlib.import_module("mt5api.main")


def test_fresh_process_import_without_environment_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unset environment key prevents a fresh application import."""
    import os  # ruff: ignore[import-outside-top-level]
    import subprocess  # ruff: ignore[import-outside-top-level, suspicious-subprocess-import]
    import sys  # ruff: ignore[import-outside-top-level]

    monkeypatch.delenv("MT5API_SECRET_KEY", raising=False)
    script = """
import sys
from unittest.mock import Mock
from tests.mt5_constants import install_mt5_constants
mt5 = Mock()
mt5.__name__ = 'MetaTrader5'
install_mt5_constants(mt5)
sys.modules['MetaTrader5'] = mt5
import mt5api.main
"""
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    assert result.returncode != 0
    assert "MT5API_SECRET_KEY is required" in result.stderr
