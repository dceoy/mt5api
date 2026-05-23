"""MT5 connection management endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from pdmt5.dataframe import Mt5Config

from mt5api.auth import verify_api_key
from mt5api.dependencies import (
    get_mt5_client_lock,
    release_market_book_subscriptions,
    replace_mt5_client,
)
from mt5api.models import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["connection"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/connection/login",
    response_model=LoginResponse,
    summary="Login to MT5 terminal",
    description=(
        "Reconnect the MT5 terminal using the supplied credentials. The current "
        "MT5 client (if any) is shut down and any active market-book "
        "subscriptions are released before the new connection is established."
    ),
)
async def post_connection_login(
    app_request: Request,
    request: LoginRequest,
) -> LoginResponse:
    """Reconnect the MT5 singleton with new credentials.

    Args:
        app_request: FastAPI request, used to access the application state for
            market-book subscription cleanup.
        request: Login parameters (login, password, server, timeout).

    Returns:
        LoginResponse describing the new connection. The password is never
        echoed.
    """
    config = Mt5Config(
        login=request.login,
        password=request.password.get_secret_value(),
        server=request.server,
        timeout=request.timeout,
    )

    async with get_mt5_client_lock():
        await release_market_book_subscriptions(app_request.app)
        await replace_mt5_client(config)

    logger.info(
        "MT5 client reconnected (login=%d, server=%s)",
        request.login,
        request.server,
    )
    return LoginResponse(
        login=request.login,
        server=request.server,
        timeout=request.timeout,
        connected=True,
    )
