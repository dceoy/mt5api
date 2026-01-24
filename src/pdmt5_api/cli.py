"""Command-line interface for the pdmt5 REST API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import uvicorn

from pdmt5_api.rest.app import create_app


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the pdmt5 REST API server.")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Bind port (default: 8000)."
    )
    parser.add_argument(
        "--log-level", default="info", help="Uvicorn log level (default: info)."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON file with pdmt5 initialization settings.",
    )
    return parser.parse_args(argv)


def _load_config(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in config file: {path}") from exc


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    config = _load_config(args.config)
    app = create_app(config=config)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
