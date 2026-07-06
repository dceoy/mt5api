"""Health check and system information endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from pdmt5.dataframe import Mt5DataClient  # noqa: TC002

from mt5api.auth import verify_api_key
from mt5api.constants import API_VERSION
from mt5api.dependencies import (
    get_mt5_client,
    get_response_format,
    run_in_threadpool,
)
from mt5api.formatters import format_response
from mt5api.models import DataResponse, HealthResponse, ResponseFormat

if TYPE_CHECKING:
    from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API and MT5 terminal connection status",
)
async def get_health() -> HealthResponse:
    """Check API health and MT5 terminal connectivity.

    This endpoint does NOT require authentication (public health check).
    Returns 200 OK even if MT5 is unavailable to allow infrastructure
    health monitoring without failing on MT5 outages.

    Returns:
        HealthResponse with API and MT5 connection status.
    """
    mt5_connected = False
    mt5_version = None

    try:
        client = await run_in_threadpool(get_mt5_client)
        version_dict = await run_in_threadpool(client.version_as_dict)
        if version_dict:
            mt5_version = f"{version_dict.get('mt5_terminal_version', 'unknown')}"
        mt5_connected = True
    except Exception as e:  # noqa: BLE001
        logger.debug("MT5 not available for health check: %s", e)

    return HealthResponse(
        status="healthy" if mt5_connected else "unhealthy",
        mt5_connected=mt5_connected,
        mt5_version=mt5_version,
        api_version=API_VERSION,
    )


@router.get(
    "/version",
    response_model=DataResponse,
    summary="Get MT5 version",
    description="Get MetaTrader 5 terminal version information",
    dependencies=[Depends(verify_api_key)],
)
async def get_version(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
) -> DataResponse | Response:
    """Get MT5 terminal version information.

    Args:
        mt5_client: MT5 data client dependency.
        response_format: Negotiated response format (JSON or Parquet).

    Returns:
        JSON or Parquet response with version data.
    """
    version_dict = await run_in_threadpool(mt5_client.version_as_dict)
    return format_response(version_dict, response_format)


@router.get(
    "/last-error",
    response_model=DataResponse,
    summary="Get last MT5 error",
    description="Get the last error information from the MetaTrader 5 terminal",
    dependencies=[Depends(verify_api_key)],
)
async def get_last_error(
    mt5_client: Annotated[Mt5DataClient, Depends(get_mt5_client)],
    response_format: Annotated[ResponseFormat, Depends(get_response_format)],
) -> DataResponse | Response:
    """Get the last MT5 error information.

    Args:
        mt5_client: MT5 data client dependency.
        response_format: Negotiated response format (JSON or Parquet).

    Returns:
        JSON or Parquet response with last error data.
    """
    error_dict = await run_in_threadpool(mt5_client.last_error_as_dict)
    return format_response(error_dict, response_format)
