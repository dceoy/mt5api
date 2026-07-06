"""Tests for API module entrypoint."""

from __future__ import annotations

import runpy
import sys

import pytest
import uvicorn

from mt5api.constants import (
    API_APP_IMPORT,
    DEFAULT_API_HOST,
    ENV_MT5API_HOST,
    ENV_MT5API_LOG_LEVEL,
    ENV_MT5API_PORT,
)


def test_main_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should use default host/port/log level."""
    monkeypatch.delenv(ENV_MT5API_HOST, raising=False)
    monkeypatch.delenv(ENV_MT5API_PORT, raising=False)
    monkeypatch.delenv(ENV_MT5API_LOG_LEVEL, raising=False)

    captured_args: tuple[object, ...] | None = None
    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_args, captured_kwargs
        captured_args = _args
        captured_kwargs = kwargs

    from mt5api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_args == (API_APP_IMPORT,)
    assert captured_kwargs is not None
    assert captured_kwargs["host"] == DEFAULT_API_HOST
    assert captured_kwargs["port"] == 8000
    assert captured_kwargs["log_level"] == "info"


def test_main_uses_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should respect configured environment variables."""
    monkeypatch.setenv(ENV_MT5API_HOST, "127.0.0.1")
    monkeypatch.setenv(ENV_MT5API_PORT, "9001")
    monkeypatch.setenv(ENV_MT5API_LOG_LEVEL, "WARNING")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    from mt5api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_kwargs is not None
    assert captured_kwargs["host"] == "127.0.0.1"
    assert captured_kwargs["port"] == 9001
    assert captured_kwargs["log_level"] == "warning"


def test_main_handles_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should fail fast on an invalid port value."""
    monkeypatch.setenv(ENV_MT5API_PORT, "not-a-number")

    from mt5api import __main__ as api_main  # noqa: PLC0415

    with pytest.raises(ValueError, match="Invalid MT5API_PORT"):
        api_main.main()


def test_main_handles_out_of_range_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should fail fast on an out-of-range port value."""
    monkeypatch.setenv(ENV_MT5API_PORT, "70000")

    from mt5api import __main__ as api_main  # noqa: PLC0415

    with pytest.raises(ValueError, match="Invalid MT5API_PORT"):
        api_main.main()


def test_main_accepts_trace_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should pass uvicorn-supported trace logging through."""
    monkeypatch.setenv(ENV_MT5API_LOG_LEVEL, "trace")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    from mt5api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_kwargs is not None
    assert captured_kwargs["log_level"] == "trace"


def test_module_entrypoint_invokes_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running the module should invoke main()."""
    monkeypatch.setenv(ENV_MT5API_PORT, "8001")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    monkeypatch.setattr(uvicorn, "run", fake_run)

    sys.modules.pop("mt5api.__main__", None)
    runpy.run_module("mt5api.__main__", run_name="__main__")

    assert captured_kwargs is not None
    assert captured_kwargs["port"] == 8001
