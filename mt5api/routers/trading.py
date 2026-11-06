"""Operational endpoints for order checks and terminal subscriptions."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pdmt5.dataframe import Mt5DataClient  # ruff: ignore[typing-only-third-party-import]

from mt5api.auth import is_auth_enabled, verify_api_key
from mt5api.constants import (
    ENV_MT5API_ENABLE_ORDER_SEND,
    ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
)
from mt5api.dependencies import (
    get_mt5_client,
    get_mt5_runtime_state,
    get_response_format,
    run_in_threadpool,
)
from mt5api.formatters import format_response
from mt5api.models import (
    DataResponse,
    ErrorResponse,
    MarketBookSubscriptionRequest,
    OrderCheckRequest,
    OrderSendRequest,
    ResponseFormat,
    SymbolSelectRequest,
)

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(tags=["trading"], dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


def _build_market_book_subscription_limit_response(
    app_request: Request,
    *,
    limit: int,
) -> JSONResponse:
    """Create a problem-details response for subscription exhaustion.

    Returns:
        HTTP 429 problem-details response.
    """
    error = ErrorResponse(
        type="/errors/subscription-limit",
        title="Subscription Limit Exceeded",
        status=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=(
            "Active market-book subscriptions are limited to "
            f"{limit}. Unsubscribe from an existing symbol or increase "
            f"{ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS}."
        ),
        instance=str(app_request.url),
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error.model_dump(),
    )


def require_order_send_access() -> None:
    """Reject live trading unless explicitly enabled with API-key authentication.

    Raises:
        HTTPException: If the endpoint is disabled or authentication is unconfigured.
    """
    enabled = os.getenv(ENV_MT5API_ENABLE_ORDER_SEND, "").strip().lower()
    if enabled not in {"1", "true"} or not is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Live trading is disabled. Set MT5API_ENABLE_ORDER_SEND=true "
                "and configure MT5API_SECRET_KEY to allow order submission."
            ),
        )


@router.post(
    "/order/send",
    response_model=DataResponse,
    summary="Send live trading order (opt-in)",
    description=(
        "Submit a live MetaTrader5 order. Disabled unless MT5API_ENABLE_ORDER_SEND "
        "is true and API-key authentication is configured. Check the returned "
        "MT5 retcode: HTTP 200 does not imply the order was filled."
    ),
    dependencies=[Depends(require_order_send_access)],
)
async def post_order_send(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: OrderSendRequest,
) -> DataResponse | Response:
    """Send a validated order and preserve the MT5 execution result.

    Returns:
        MT5 order-send result, including retcode, in JSON or Parquet format.
    """
    payload = request.request.to_mt5_dict()
    result: dict[str, Any] = await run_in_threadpool(
        mt5_client.order_send_as_dict,
        request=payload,
    )
    return format_response(result, response_format)


@router.post(
    "/order/check",
    response_model=DataResponse,
    summary="Check order",
    description="Check funds sufficiency for performing a trading operation",
)
async def post_order_check(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: OrderCheckRequest,
) -> DataResponse | Response:
    """Check funds sufficiency for a trading operation.

    Returns:
        JSON or Parquet representation of the order-check result.
    """
    result: dict[str, Any] = await run_in_threadpool(
        mt5_client.order_check_as_dict,
        request=request.request.to_mt5_dict(),
    )
    return format_response(result, response_format)


@router.post(
    "/symbols/{symbol}/select",
    response_model=DataResponse,
    summary="Select symbol",
    description=(
        "Select a symbol in the MarketWatch window or remove it from the window"
    ),
)
async def post_symbol_select(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[SymbolSelectRequest, Depends()],
) -> DataResponse | Response:
    """Select or deselect a symbol in the MarketWatch window.

    Returns:
        JSON or Parquet representation of the selection result.
    """
    success = await run_in_threadpool(
        mt5_client.symbol_select,
        symbol=request.symbol,
        enable=request.enable,
    )
    return format_response(
        {"symbol": request.symbol, "enable": request.enable, "success": success},
        response_format,
    )


@router.post(
    "/market-book/{symbol}/subscribe",
    response_model=DataResponse,
    summary="Subscribe to market depth (experimental)",
    description="**Experimental.** Subscribe to Market Depth events for a symbol",
)
async def post_market_book_subscribe(
    app_request: Request,
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[MarketBookSubscriptionRequest, Depends()],
) -> DataResponse | Response:
    """Subscribe to market depth for a symbol.

    Returns:
        Subscription result or an HTTP 429 problem response.
    """
    state = get_mt5_runtime_state(app_request)
    subscriptions = state.market_book_subscriptions
    symbol = request.symbol
    if (
        symbol not in subscriptions
        and len(subscriptions) >= state.max_market_book_subscriptions
    ):
        logger.warning(
            "Market-book subscription limit reached for %s (%d active)",
            symbol,
            len(subscriptions),
        )
        return _build_market_book_subscription_limit_response(
            app_request,
            limit=state.max_market_book_subscriptions,
        )

    success = await run_in_threadpool(mt5_client.market_book_add, symbol=symbol)
    if success:
        subscriptions.add(symbol)
        state.market_book_cleanup_client = mt5_client
    return format_response(
        {"symbol": symbol, "subscribed": success},
        response_format,
    )


@router.post(
    "/market-book/{symbol}/unsubscribe",
    response_model=DataResponse,
    summary="Unsubscribe from market depth (experimental)",
    description="**Experimental.** Cancel Market Depth subscription for a symbol",
)
async def post_market_book_unsubscribe(
    app_request: Request,
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[MarketBookSubscriptionRequest, Depends()],
) -> DataResponse | Response:
    """Unsubscribe from market depth for a symbol.

    Returns:
        JSON or Parquet representation of the unsubscribe result.
    """
    symbol = request.symbol
    success = await run_in_threadpool(mt5_client.market_book_release, symbol=symbol)
    if success:
        state = get_mt5_runtime_state(app_request)
        state.market_book_subscriptions.discard(symbol)
        if not state.market_book_subscriptions:
            state.market_book_cleanup_client = None
    return format_response(
        {"symbol": symbol, "unsubscribed": success},
        response_format,
    )
