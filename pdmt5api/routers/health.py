"""Health check and system information endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends

from pdmt5.api.auth import verify_api_key
from pdmt5.api.dependencies import (
    get_mt5_client,
    get_response_format,
    run_in_threadpool,
)
from pdmt5.api.formatters import format_response
from pdmt5.api.models import DataResponse, HealthResponse, ResponseFormat
from pdmt5.dataframe import Mt5DataClient  # noqa: TC001

if TYPE_CHECKING:
    from fastapi.responses import Response

API_VERSION = "1.0.0"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])


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
        client = get_mt5_client()
        mt5_connected = True
        version_dict = await run_in_threadpool(client.version_as_dict)
        if version_dict:
            mt5_version = f"{version_dict.get('version', 'unknown')}"
    except RuntimeError as e:
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
