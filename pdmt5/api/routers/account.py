"""Account and terminal information endpoints."""

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
from pdmt5.api.models import DataResponse, ResponseFormat
from pdmt5.dataframe import Mt5DataClient  # noqa: TC001

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    prefix="/api/v1",
    tags=["account"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/account",
    response_model=DataResponse,
    summary="Get account info",
    description="Get MetaTrader 5 account information",
)
async def get_account_info(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
) -> DataResponse | Response:
    """Get account information.

    Args:
        mt5_client: MT5 data client dependency.
        response_format: Negotiated response format (JSON or Parquet).

    Returns:
        JSON or Parquet response with account data.
    """
    dataframe = await run_in_threadpool(mt5_client.account_info_as_df)
    return format_response(dataframe, response_format)


@router.get(
    "/terminal",
    response_model=DataResponse,
    summary="Get terminal info",
    description="Get MetaTrader 5 terminal information",
)
async def get_terminal_info(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
) -> DataResponse | Response:
    """Get terminal information.

    Args:
        mt5_client: MT5 data client dependency.
        response_format: Negotiated response format (JSON or Parquet).

    Returns:
        JSON or Parquet response with terminal data.
    """
    dataframe = await run_in_threadpool(mt5_client.terminal_info_as_df)
    return format_response(dataframe, response_format)
