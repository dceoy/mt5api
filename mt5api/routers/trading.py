"""Operational endpoints for order checks and terminal subscriptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends, Path, Request
from pdmt5.dataframe import Mt5DataClient  # noqa: TC002

from mt5api.auth import verify_api_key
from mt5api.dependencies import (
    get_mt5_client,
    get_response_format,
    run_in_threadpool,
)
from mt5api.formatters import format_response
from mt5api.models import (
    DataResponse,
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

_ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY = "active_market_book_subscriptions"
_MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY = "market_book_cleanup_client"


def _get_active_market_book_subscriptions(request: Request) -> set[str]:
    """Return the active market-book subscription set for the application."""
    return cast(
        "set[str]",
        getattr(request.app.state, _ACTIVE_MARKET_BOOK_SUBSCRIPTIONS_STATE_KEY),
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
    summary="Subscribe to market depth",
    description="Subscribe to Market Depth change events for a symbol",
)
async def post_market_book_subscribe(
    request: Request,
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    symbol: Annotated[str, Path(min_length=1, max_length=32)],
) -> DataResponse | Response:
    """Subscribe to market depth for a symbol.

    Returns:
        JSON or Parquet response with subscription result.
    """
    success = await run_in_threadpool(
        mt5_client.market_book_add,
        symbol=symbol,
    )
    if success:
        subscriptions = _get_active_market_book_subscriptions(request)
        subscriptions.add(symbol)
        setattr(request.app.state, _MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, mt5_client)
    return format_response(
        {"symbol": symbol, "subscribed": success},
        response_format,
    )


@router.post(
    "/market-book/{symbol}/unsubscribe",
    response_model=DataResponse,
    summary="Unsubscribe from market depth",
    description="Cancel Market Depth subscription for a symbol",
)
async def post_market_book_unsubscribe(
    request: Request,
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    symbol: Annotated[str, Path(min_length=1, max_length=32)],
) -> DataResponse | Response:
    """Unsubscribe from market depth for a symbol.

    Returns:
        JSON or Parquet response with unsubscription result.
    """
    success = await run_in_threadpool(
        mt5_client.market_book_release,
        symbol=symbol,
    )
    if success:
        subscriptions = _get_active_market_book_subscriptions(request)
        subscriptions.discard(symbol)
        if not subscriptions:
            setattr(request.app.state, _MARKET_BOOK_CLEANUP_CLIENT_STATE_KEY, None)
    return format_response(
        {"symbol": symbol, "unsubscribed": success},
        response_format,
    )
