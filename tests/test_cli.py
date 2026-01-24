"""Tests for API module entrypoint."""

from __future__ import annotations

import runpy
import sys
from typing import TYPE_CHECKING

import uvicorn

if TYPE_CHECKING:
    import pytest


def test_main_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should use default host/port/log level."""
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("API_LOG_LEVEL", raising=False)

    captured_args: tuple[object, ...] | None = None
    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_args, captured_kwargs
        captured_args = _args
        captured_kwargs = kwargs

    from pdmt5.api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_args == ("pdmt5.api.main:app",)
    assert captured_kwargs is not None
    assert (
        captured_kwargs["host"] == api_main._DEFAULT_HOST  # pyright: ignore[reportPrivateUsage]
    )
    assert captured_kwargs["port"] == 8000
    assert captured_kwargs["log_level"] == "info"


def test_main_uses_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should respect configured environment variables."""
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("API_LOG_LEVEL", "WARNING")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    from pdmt5.api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_kwargs is not None
    assert captured_kwargs["host"] == "127.0.0.1"
    assert captured_kwargs["port"] == 9001
    assert captured_kwargs["log_level"] == "warning"


def test_main_handles_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should fall back to default port on invalid value."""
    monkeypatch.setenv("API_PORT", "not-a-number")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    from pdmt5.api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_kwargs is not None
    assert captured_kwargs["port"] == 8000


def test_main_handles_out_of_range_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should fall back to default port on out-of-range value."""
    monkeypatch.setenv("API_PORT", "70000")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    from pdmt5.api import __main__ as api_main  # noqa: PLC0415

    monkeypatch.setattr(api_main.uvicorn, "run", fake_run)

    api_main.main()

    assert captured_kwargs is not None
    assert captured_kwargs["port"] == 8000


def test_module_entrypoint_invokes_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running the module should invoke main()."""
    monkeypatch.setenv("API_PORT", "8001")

    captured_kwargs: dict[str, object] | None = None

    def fake_run(*_args: object, **kwargs: object) -> None:
        nonlocal captured_kwargs
        captured_kwargs = kwargs

    monkeypatch.setattr(uvicorn, "run", fake_run)

    sys.modules.pop("pdmt5.api.__main__", None)
    runpy.run_module("pdmt5.api.__main__", run_name="__main__")

    assert captured_kwargs is not None
    assert captured_kwargs["port"] == 8001
