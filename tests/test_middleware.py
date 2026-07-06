# pyright: reportPrivateUsage=false
"""Tests for API middleware behavior."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pdmt5.mt5 import Mt5RuntimeError
from pydantic import BaseModel

from mt5api.middleware import _create_error_response, add_middleware

if TYPE_CHECKING:
    from collections.abc import Callable


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
        "/test",
    )

    assert response.status_code == 400
    payload = json.loads(bytes(response.body))
    assert payload == {
        "type": "/errors/test",
        "title": "Test Error",
        "status": 400,
        "detail": "Test detail",
        "instance": "/test",
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


def test_http_exception_handler_flattens_problem_details() -> None:
    """HTTPException details should not be nested under a detail key."""

    def handler() -> None:
        raise HTTPException(
            status_code=401,
            detail={
                "type": "/errors/unauthorized",
                "title": "Authentication Required",
                "detail": "Missing API key.",
            },
        )

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert response.status_code == 401
    assert response.json() == {
        "type": "/errors/unauthorized",
        "title": "Authentication Required",
        "status": 401,
        "detail": "Missing API key.",
        "instance": "http://testserver/boom",
    }


def test_http_exception_handler_handles_plain_detail() -> None:
    """HTTPException string details should become generic problem details."""

    def handler() -> None:
        raise HTTPException(status_code=404, detail="Missing")

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert response.status_code == 404
    assert response.json() == {
        "type": "/errors/http-error",
        "title": "HTTP Error",
        "status": 404,
        "detail": "Missing",
        "instance": "http://testserver/boom",
    }


def test_request_validation_error_returns_problem_details() -> None:
    """FastAPI request validation should use RFC 7807 problem details."""
    app = FastAPI()
    add_middleware(app)

    def handler(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    app.get("/items/{item_id}")(handler)

    client = TestClient(app)
    response = client.get("/items/not-an-int")

    assert response.status_code == 422
    payload = response.json()
    assert payload["type"] == "/errors/validation-error"
    assert payload["title"] == "Request Validation Failed"
    assert payload["status"] == 422
    assert "item_id" in payload["detail"]
    assert payload["instance"] == "http://testserver/items/not-an-int"


def test_logging_middleware_adds_process_time_header() -> None:
    """Test logging middleware adds timing header."""

    def handler() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(_create_app(handler))
    response = client.get("/boom")

    assert "X-Process-Time" in response.headers
