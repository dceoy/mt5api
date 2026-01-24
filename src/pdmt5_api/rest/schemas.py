"""Pydantic models for REST API payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OperationResult(BaseModel):
    success: bool = Field(..., description="True if the operation succeeded.")
    detail: Any | None = Field(default=None, description="Optional response data.")


class ConnectionRequest(BaseModel):
    path: str | None = None
    login: int | None = None
    password: str | None = None
    server: str | None = None
    timeout: int | None = None
    portable: bool | None = None
    config: dict[str, Any] | None = None


class OrderRequest(BaseModel):
    request: dict[str, Any]
