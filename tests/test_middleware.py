# pyright: reportPrivateUsage=false
"""Tests for API middleware behavior."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from pdmt5.api.middleware import _create_error_response, add_middleware
from pdmt5.mt5 import Mt5RuntimeError

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest


def _create_app(handler: Callable[[], object]) -> FastAPI:
    app = FastAPI()
    add_middleware(app)
    app.get("/boom")(handler)
    return app


def test_create_error_response_builds_problem_details() -> None:
    """Test helper creates RFC 7807 error responses."""
    response = _create_error_response(
        "/errors/test",
        "Test Error",
        400,
        "Test detail",
        "/api/v1/test",
    )

    assert response.status_code == 400
    payload = json.loads(bytes(response.body))
    assert payload == {
        "type": "/errors/test",
        "title": "Test Error",
        "status": 400,
        "detail": "Test detail",
        "instance": "/api/v1/test",
    }


def test_error_handler_handles_mt5_runtime_error() -> None:
    """Test Mt5RuntimeError mapping to 503 response."""

    class DummyMt5Error(Mt5RuntimeError):
        """Test-specific MT5 error."""

    def handler() -> None:
        raise DummyMt5Error

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert (response.status_code, response.json()["type"]) == (
        503,
        "/errors/mt5-error",
    )


def test_error_handler_handles_validation_error() -> None:
    """Test ValidationError mapping to 400 response."""

    class Payload(BaseModel):
        value: int

    def handler() -> None:
        Payload(value=cast("int", "bad"))

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert (response.status_code, response.json()["type"]) == (
        400,
        "/errors/validation-error",
    )


def test_error_handler_handles_value_error() -> None:
    """Test ValueError mapping to 400 response."""

    class DummyValueError(ValueError):
        """Test-specific value error."""

    def handler() -> None:
        raise DummyValueError

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert (response.status_code, response.json()["type"]) == (
        400,
        "/errors/invalid-input",
    )


def test_error_handler_handles_runtime_error() -> None:
    """Test RuntimeError mapping to 503 response."""

    class DummyRuntimeError(RuntimeError):
        """Test-specific runtime error."""

    def handler() -> None:
        raise DummyRuntimeError

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert (response.status_code, response.json()["type"]) == (
        503,
        "/errors/runtime-error",
    )


def test_error_handler_handles_unexpected_error() -> None:
    """Test unexpected error mapping to 500 response."""

    class UnexpectedError(Exception):
        """Test-specific unexpected error."""

    def handler() -> None:
        raise UnexpectedError

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert (response.status_code, response.json()["type"]) == (
        500,
        "/errors/internal-error",
    )


def test_logging_middleware_adds_process_time_header() -> None:
    """Test logging middleware adds timing header."""

    def handler() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert "X-Process-Time" in response.headers


def test_rate_limiting_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test rate limiting returns 429 when limit exceeded."""
    monkeypatch.setenv("API_RATE_LIMIT", "1")

    app = FastAPI()
    add_middleware(app)

    def limited() -> dict[str, str]:
        return {"status": "ok"}

    app.get("/limited")(limited)

    client = TestClient(app)

    first = client.get("/limited")
    second = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 429
