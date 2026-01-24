"""Symbol-related API endpoints."""

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
    ResponseFormat,
    SymbolInfoRequest,
    SymbolsRequest,
    SymbolTickRequest,
)
from pdmt5.dataframe import Mt5DataClient  # noqa: TC001

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    prefix="/api/v1",
    tags=["symbols"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/symbols",
    response_model=DataResponse,
    summary="List symbols",
    description="Get list of available trading symbols with optional filtering",
)
async def get_symbols(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[SymbolsRequest, Depends()],
) -> DataResponse | Response:
    """Get list of symbols with optional group filter.

    Returns:
        JSON or Parquet response with symbol data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.symbols_get_as_df,
        group=request.group,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/symbols/{symbol}",
    response_model=DataResponse,
    summary="Get symbol info",
    description="Get detailed information for a specific symbol",
)
async def get_symbol_info(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[SymbolInfoRequest, Depends()],
) -> DataResponse | Response:
    """Get detailed information for a specific symbol.

    Returns:
        JSON or Parquet response with symbol info.
    """
    dataframe = await run_in_threadpool(
        mt5_client.symbol_info_as_df,
        symbol=request.symbol,
    )
    return format_response(dataframe, response_format)


@router.get(
    "/symbols/{symbol}/tick",
    response_model=DataResponse,
    summary="Get symbol tick",
    description="Get latest tick data for a specific symbol",
)
async def get_symbol_tick(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[SymbolTickRequest, Depends()],
) -> DataResponse | Response:
    """Get latest tick data for a symbol.

    Returns:
        JSON or Parquet response with tick data.
    """
    dataframe = await run_in_threadpool(
        mt5_client.symbol_info_tick_as_df,
        symbol=request.symbol,
    )
    return format_response(dataframe, response_format)
