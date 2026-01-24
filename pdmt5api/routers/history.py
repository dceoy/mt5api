"""History, positions, and orders endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends

from pdmt5.api.auth import verify_api_key
from pdmt5.api.dependencies import (
    get_mt5_client,
    get_response_format,
    run_in_threadpool,
)
from pdmt5.api.formatters import format_response
from pdmt5.api.models import (
    DataResponse,
    HistoryDealsRequest,
    HistoryOrdersRequest,
    OrdersRequest,
    PositionsRequest,
    ResponseFormat,
)
from pdmt5.dataframe import Mt5DataClient  # noqa: TC001

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    prefix="/api/v1",
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
