"""Trading operation endpoints (order check, order send, symbol select)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends
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
    OrderSendRequest,
    ResponseFormat,
    SymbolSelectRequest,
)

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    tags=["trading"],
    dependencies=[Depends(verify_api_key)],
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
        request=request.request,
    )
    return format_response(result, response_format)


@router.post(
    "/order/send",
    response_model=DataResponse,
    summary="Send order",
    description="Send a trading operation request to the trade server",
)
async def post_order_send(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: OrderSendRequest,
) -> DataResponse | Response:
    """Send a trade request to the trade server.

    Returns:
        JSON or Parquet response with order send result.
    """
    result: dict[str, Any] = await run_in_threadpool(
        mt5_client.order_send_as_dict,
        request=request.request,
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
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    symbol: str,
) -> DataResponse | Response:
    """Subscribe to market depth for a symbol.

    Returns:
        JSON or Parquet response with subscription result.
    """
    success = await run_in_threadpool(
        mt5_client.market_book_add,
        symbol=symbol,
    )
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
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    symbol: str,
) -> DataResponse | Response:
    """Unsubscribe from market depth for a symbol.

    Returns:
        JSON or Parquet response with unsubscription result.
    """
    success = await run_in_threadpool(
        mt5_client.market_book_release,
        symbol=symbol,
    )
    return format_response(
        {"symbol": symbol, "unsubscribed": success},
        response_format,
    )
