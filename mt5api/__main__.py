"""Module entrypoint for running the MT5 REST API."""

from __future__ import annotations

import logging

import uvicorn

from .constants import (
    API_APP_IMPORT,
    DEFAULT_API_PORT,
    MAX_API_PORT,
    get_configured_api_host,
    get_configured_api_log_level,
    get_configured_api_port,
)


def _get_host() -> str:
    """Get API host from environment.

    Returns:
        Host address to bind the API server to.
    """
    return get_configured_api_host()


def _get_port() -> int:
    """Get API port from environment.

    Returns:
        Port number for the API server.
    """
    raw_port = get_configured_api_port()
    if raw_port is None:
        return DEFAULT_API_PORT

    try:
        port_value = int(raw_port)
    except ValueError:
        return DEFAULT_API_PORT

    if not 1 <= port_value <= MAX_API_PORT:
        return DEFAULT_API_PORT

    return port_value


def _get_log_level() -> str:
    """Get log level from environment.

    Returns:
        Log level string for uvicorn.
    """
    return get_configured_api_log_level().lower()


def main() -> None:
    """Run the MT5 REST API with uvicorn."""
    host = _get_host()
    port = _get_port()
    log_level = _get_log_level()

    logging.getLogger(__name__).info("Starting MT5 REST API on %s:%s", host, port)
    uvicorn.run(
        API_APP_IMPORT,
        host=host,
        port=port,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
