"""FastAPI application factory for pdmt5 REST API."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from pdmt5_api.rest.router import router
from pdmt5_api.rest.service import configure_service
from pdmt5_api.rest.upstream import load_upstream_app


def create_app(config: dict[str, Any] | None = None) -> FastAPI:
    upstream_app = load_upstream_app(config)
    if upstream_app is not None:
        return upstream_app

    app = FastAPI(title="pdmt5 REST API", version="0.1.0")
    if config:
        configure_service(config)
    app.include_router(router)
    return app
