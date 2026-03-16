"""History, positions, and orders endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

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
    HistoryDealsRequest,
    HistoryOrdersRequest,
    HistoryTotalRequest,
    OrdersRequest,
    PositionsRequest,
    ResponseFormat,
)

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    tags=["history"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/history/orders",
    response_model=DataResponse,
    summary="Get historical orders",
    description="Get historical orders with date range or ticket/position filters",
)
async def get_history_orders(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[HistoryOrdersRequest, Depends()],
) -> DataResponse | Response:
    """Get historical orders.

    Returns:
        JSON or Parquet response with order data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.history_orders_get_as_df,
        date_from=request.date_from,
        date_to=request.date_to,
        group=request.group,
        symbol=request.symbol,
        ticket=request.ticket,
        position=request.position,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/history/deals",
    response_model=DataResponse,
    summary="Get historical deals",
    description="Get historical deals with date range or ticket/position filters",
)
async def get_history_deals(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[HistoryDealsRequest, Depends()],
) -> DataResponse | Response:
    """Get historical deals.

    Returns:
        JSON or Parquet response with deal data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.history_deals_get_as_df,
        date_from=request.date_from,
        date_to=request.date_to,
        group=request.group,
        symbol=request.symbol,
        ticket=request.ticket,
        position=request.position,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/positions",
    response_model=DataResponse,
    summary="Get open positions",
    description="Get current open positions with optional filters",
)
async def get_positions(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[PositionsRequest, Depends()],
) -> DataResponse | Response:
    """Get current open positions.

    Returns:
        JSON or Parquet response with position data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.positions_get_as_df,
        symbol=request.symbol,
        group=request.group,
        ticket=request.ticket,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/orders",
    response_model=DataResponse,
    summary="Get pending orders",
    description="Get current pending orders with optional filters",
)
async def get_orders(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[OrdersRequest, Depends()],
) -> DataResponse | Response:
    """Get current pending orders.

    Returns:
        JSON or Parquet response with order data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.orders_get_as_df,
        symbol=request.symbol,
        group=request.group,
        ticket=request.ticket,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/orders/total",
    response_model=DataResponse,
    summary="Get active orders count",
    description="Get the total number of active orders",
)
async def get_orders_total(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
) -> DataResponse | Response:
    """Get the total number of active orders.

    Returns:
        JSON or Parquet response with total count.
    """
    total = await run_in_threadpool(mt5_client.orders_total)
    return format_response({"total": total}, response_format)


@router.get(
    "/positions/total",
    response_model=DataResponse,
    summary="Get open positions count",
    description="Get the total number of open positions",
)
async def get_positions_total(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
) -> DataResponse | Response:
    """Get the total number of open positions.

    Returns:
        JSON or Parquet response with total count.
    """
    total = await run_in_threadpool(mt5_client.positions_total)
    return format_response({"total": total}, response_format)


@router.get(
    "/history/orders/total",
    response_model=DataResponse,
    summary="Get historical orders count",
    description="Get the total number of historical orders in a date range",
)
async def get_history_orders_total(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[HistoryTotalRequest, Depends()],
) -> DataResponse | Response:
    """Get the total number of historical orders.

    Returns:
        JSON or Parquet response with total count.
    """
    total = await run_in_threadpool(
        mt5_client.history_orders_total,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    return format_response({"total": total}, response_format)


@router.get(
    "/history/deals/total",
    response_model=DataResponse,
    summary="Get historical deals count",
    description="Get the total number of historical deals in a date range",
)
async def get_history_deals_total(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[HistoryTotalRequest, Depends()],
) -> DataResponse | Response:
    """Get the total number of historical deals.

    Returns:
        JSON or Parquet response with total count.
    """
    total = await run_in_threadpool(
        mt5_client.history_deals_total,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    return format_response({"total": total}, response_format)
