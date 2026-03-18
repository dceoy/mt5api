"""Operational endpoints for order checks and terminal subscriptions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pdmt5.dataframe import Mt5DataClient  # noqa: TC002

from mt5api.auth import verify_api_key
from mt5api.constants import (
    ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
    ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS,
    MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY,
    MAX_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY,
)
from mt5api.dependencies import (
    get_mt5_client,
    get_response_format,
    run_in_threadpool,
)
from mt5api.formatters import format_response
from mt5api.models import (
    DataResponse,
    ErrorResponse,
    MarketBookSubscriptionRequest,
    OrderCheckRequest,
    ResponseFormat,
    SymbolSelectRequest,
)

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    tags=["trading"],
    dependencies=[Depends(verify_api_key)],
)
logger = logging.getLogger(__name__)


def _get_active_market_book_subscriptions(app_request: Request) -> set[str]:
    """Return the active market-book subscription set for the application."""
    return cast(
        "set[str]",
        getattr(app_request.app.state, ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY),
    )


def _get_max_market_book_subscriptions(app_request: Request) -> int:
    """Return the configured market-book subscription limit for the application."""
    return cast(
        "int",
        getattr(app_request.app.state, MAX_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY),
    )


def _build_market_book_subscription_limit_response(
    app_request: Request,
    *,
    limit: int,
) -> JSONResponse:
    """Create a problem-details response for market-book subscription exhaustion.

    Returns:
        JSON response describing the subscription-cap violation.
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
        JSON or Parquet response with order check result.
    """
    result: dict[str, Any] = await run_in_threadpool(
        mt5_client.order_check_as_dict,
        request=request.request.model_dump(mode="python", exclude_none=True),
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
        JSON or Parquet response with selection result.
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
        JSON or Parquet response with subscription result.
    """
    subscriptions = _get_active_market_book_subscriptions(app_request)
    symbol = request.symbol
    if symbol not in subscriptions:
        max_subscriptions = _get_max_market_book_subscriptions(app_request)
        if len(subscriptions) >= max_subscriptions:
            logger.warning(
                "Market-book subscription limit reached for %s (%d active)",
                symbol,
                len(subscriptions),
            )
            return _build_market_book_subscription_limit_response(
                app_request,
                limit=max_subscriptions,
            )

    success = await run_in_threadpool(
        mt5_client.market_book_add,
        symbol=symbol,
    )
    if success:
        subscriptions.add(symbol)
        setattr(
            app_request.app.state,
            MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY,
            mt5_client,
        )
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
        JSON or Parquet response with unsubscription result.
    """
    symbol = request.symbol
    success = await run_in_threadpool(
        mt5_client.market_book_release,
        symbol=symbol,
    )
    if success:
        subscriptions = _get_active_market_book_subscriptions(app_request)
        subscriptions.discard(symbol)
        if not subscriptions:
            setattr(app_request.app.state, MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
    return format_response(
        {"symbol": symbol, "unsubscribed": success},
        response_format,
    )
