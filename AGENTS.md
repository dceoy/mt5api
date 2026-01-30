# Repository Guidelines

## Project Structure & Module Organization

The core application lives in the `mt5api/` package, with request handlers organized under `mt5api/routers/` by API surface area. Tests are in `tests/` and should mirror the module layout. Documentation lives in `docs/`, while feature and design notes live in `specs/`. The MkDocs site is configured by `mkdocs.yml` and should be kept aligned with `docs/` content.

## Build, Test, and Development Commands

Use `uv` for all environment and task execution. Typical commands: `uv sync` to install dependencies; `uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000` to run the API; `uv run pytest` for tests; `uv run ruff check .` and `uv run ruff format .` for lint/format; `uv run pyright` for type checks; `uv run mkdocs serve` for local docs preview.

## Coding Style & Naming Conventions

Ruff is authoritative with line length 88. Pyright runs in strict mode. Use Google-style docstrings for public modules, classes, and functions. Name modules and functions in `snake_case`, classes in `CapWords`, and tests in files named `test_*.py`.

## Testing Guidelines

Use `pytest` with `pytest-asyncio` for async coverage. Enforce coverage via `pytest-cov` with a `fail_under` target of 100. New features must include tests that cover success, error, and edge cases, keeping `tests/` organized by feature area.

## Commit & Pull Request Guidelines

Commit messages must be sentence-case and imperative, e.g., "Fix QA checks and docs" or "Bump python-multipart". Keep PRs focused, include test updates, and note any changes to `docs/` or `specs/` when behavior or interfaces change.

## Security & Configuration Tips

`MT5_API_KEY` is required for authenticated access. Configure `API_RATE_LIMIT` and `API_CORS_ORIGINS` per environment and never commit secrets. Runtime access depends on a Windows host with an installed and running MetaTrader 5 terminal; ensure the terminal is available before starting the API.
