"""Trading calculation endpoints (margin and profit)."""

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
    CalcMarginRequest,
    CalcProfitRequest,
    DataResponse,
    ResponseFormat,
)

if TYPE_CHECKING:
    from fastapi.responses import Response

router = APIRouter(
    tags=["calc"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/calc/margin",
    response_model=DataResponse,
    summary="Calculate margin",
    description=(
        "Calculate the margin required for a trading operation in the account currency"
    ),
)
async def get_calc_margin(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[CalcMarginRequest, Depends()],
) -> DataResponse | Response:
    """Calculate margin for a trading operation.

    Returns:
        JSON or Parquet response with calculated margin.
    """
    margin = await run_in_threadpool(
        mt5_client.order_calc_margin,
        action=request.action,
        symbol=request.symbol,
        volume=request.volume,
        price=request.price,
    )
    return format_response({"margin": margin}, response_format)


@router.get(
    "/calc/profit",
    response_model=DataResponse,
    summary="Calculate profit",
    description=(
        "Calculate the profit for a trading operation in the account currency"
    ),
)
async def get_calc_profit(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
    request: Annotated[CalcProfitRequest, Depends()],
) -> DataResponse | Response:
    """Calculate profit for a trading operation.

    Returns:
        JSON or Parquet response with calculated profit.
    """
    profit = await run_in_threadpool(
        mt5_client.order_calc_profit,
        action=request.action,
        symbol=request.symbol,
        volume=request.volume,
        price_open=request.price_open,
        price_close=request.price_close,
    )
    return format_response({"profit": profit}, response_format)
