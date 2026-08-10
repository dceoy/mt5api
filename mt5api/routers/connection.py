"""MT5 connection management endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from pdmt5.dataframe import Mt5Config

from mt5api.auth import verify_api_key
from mt5api.dependencies import (
    get_mt5_runtime_state,
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
        "MT5 client is replaced only after the new connection is established, then "
        "any active market-book subscriptions are released and cleared."
    ),
)
async def post_connection_login(
    app_request: Request,
    request: LoginRequest,
) -> LoginResponse:
    """Reconnect the application-scoped MT5 client with new credentials.

    Returns:
        Connection metadata for the newly established session.
    """
    config = Mt5Config(
        login=request.login,
        password=request.password.get_secret_value(),
        server=request.server,
        timeout=request.timeout,
    )
    state = get_mt5_runtime_state(app_request)
    async with state.client_lock:
        await replace_mt5_client(state, config)
        await release_market_book_subscriptions(state)
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
