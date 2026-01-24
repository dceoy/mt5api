"""Market data API endpoints."""

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
    MarketBookRequest,
    RatesFromPosRequest,
    RatesFromRequest,
    RatesRangeRequest,
    ResponseFormat,
    TicksFromRequest,
    TicksRangeRequest,
)
from pdmt5.dataframe import Mt5DataClient  # noqa: TC001

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    prefix="/api/v1",
    tags=["market"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/rates/from",
    response_model=DataResponse,
    summary="Get rates from date",
    description="Get historical OHLCV data from a specific date",
)
async def get_rates_from(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[RatesFromRequest, Depends()],
) -> DataResponse | Response:
    """Get historical rates from a specific date.

    Returns:
        JSON or Parquet response with OHLCV data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.copy_rates_from_as_df,
        symbol=request.symbol,
        timeframe=request.timeframe,
        date_from=request.date_from,
        count=request.count,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/rates/from-pos",
    response_model=DataResponse,
    summary="Get rates from position",
    description="Get historical OHLCV data from a specific position index",
)
async def get_rates_from_pos(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[RatesFromPosRequest, Depends()],
) -> DataResponse | Response:
    """Get historical rates from a position index.

    Returns:
        JSON or Parquet response with OHLCV data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.copy_rates_from_pos_as_df,
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_pos=request.start_pos,
        count=request.count,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/rates/range",
    response_model=DataResponse,
    summary="Get rates in range",
    description="Get historical OHLCV data for a date range",
)
async def get_rates_range(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[RatesRangeRequest, Depends()],
) -> DataResponse | Response:
    """Get historical rates in a date range.

    Returns:
        JSON or Parquet response with OHLCV data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.copy_rates_range_as_df,
        symbol=request.symbol,
        timeframe=request.timeframe,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/ticks/from",
    response_model=DataResponse,
    summary="Get ticks from date",
    description="Get tick data from a specific date",
)
async def get_ticks_from(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[TicksFromRequest, Depends()],
) -> DataResponse | Response:
    """Get tick data from a specific date.

    Returns:
        JSON or Parquet response with tick data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.copy_ticks_from_as_df,
        symbol=request.symbol,
        date_from=request.date_from,
        count=request.count,
        flags=request.flags,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/ticks/range",
    response_model=DataResponse,
    summary="Get ticks in range",
    description="Get tick data for a date range",
)
async def get_ticks_range(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[TicksRangeRequest, Depends()],
) -> DataResponse | Response:
    """Get tick data for a date range.

    Returns:
        JSON or Parquet response with tick data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.copy_ticks_range_as_df,
        symbol=request.symbol,
        date_from=request.date_from,
        date_to=request.date_to,
        flags=request.flags,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/market-book/{symbol}",
    response_model=DataResponse,
    summary="Get market book",
    description="Get market depth (DOM) for a symbol",
)
async def get_market_book(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[MarketBookRequest, Depends()],
) -> DataResponse | Response:
    """Get market depth (DOM) for a symbol.

    Returns:
        JSON or Parquet response with market book data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.market_book_get_as_df,
        symbol=request.symbol,
    )
    return format_response(dataframe, response_format)
