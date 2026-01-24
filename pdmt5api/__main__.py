"""Module entrypoint for running the MT5 REST API."""

from __future__ import annotations

import logging
import os

import uvicorn

_DEFAULT_HOST = "0.0.0.0"  # noqa: S104
_DEFAULT_PORT = 8000
_DEFAULT_LOG_LEVEL = "INFO"
_MAX_PORT = 65535


def _get_host() -> str:
    """Get API host from environment.

    Returns:
        Host address to bind the API server to.
    """
    return os.getenv("API_HOST", _DEFAULT_HOST)


def _get_port() -> int:
    """Get API port from environment.

    Returns:
        Port number for the API server.
    """
    raw_port = os.getenv("API_PORT")
    if raw_port is None:
        return _DEFAULT_PORT

    try:
        port_value = int(raw_port)
    except ValueError:
        return _DEFAULT_PORT

    if not 1 <= port_value <= _MAX_PORT:
        return _DEFAULT_PORT

    return port_value


def _get_log_level() -> str:
    """Get log level from environment.

    Returns:
        Log level string for uvicorn.
    """
    return os.getenv("API_LOG_LEVEL", _DEFAULT_LOG_LEVEL).lower()


def main() -> None:
    """Run the MT5 REST API with uvicorn."""
    host = _get_host()
    port = _get_port()
    log_level = _get_log_level()

    logging.getLogger(__name__).info("Starting MT5 REST API on %s:%s", host, port)
    uvicorn.run(
        "pdmt5.api.main:app",
        host=host,
        port=port,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
