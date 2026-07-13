# Repository Guidelines

## Project Structure & Module Organization

`mt5api/` contains the FastAPI application. Core app setup lives in `main.py`,
configuration and security in `config.py` and `auth.py`, shared request
dependencies in `dependencies.py`, middleware in `middleware.py`, response
serialization in `formatters.py`, and Pydantic/data models in `models.py`.
Endpoint modules are grouped under `mt5api/routers/` by domain, such as
`market.py`, `symbols.py`, `account.py`, and `trading.py`. Tests live in
`tests/` and mirror the package domains with `test_*.py` files. Documentation is
in `docs/`, with MkDocs configured by `mkdocs.yml`; local agent skills are under
`skills/`.

## Build, Test, and Development Commands

- `uv sync --group dev`: install runtime and development dependencies.
- `uv run python -m mt5api`: start the API using environment configuration.
- `uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000`: run the app
  directly for local API testing.
- `uv run pytest`: run the full test suite with coverage settings from
  `pyproject.toml`.
- `uv run ruff check .` and `uv run ruff format --check .`: lint and verify
  formatting.
- `uv run pyright`: run strict static type checking.
- `uv run mkdocs serve`: preview documentation locally.
- `.agents/skills/local-qa/scripts/qa.sh`: run the repository QA workflow after
  any file update. This wraps formatting, linting, type checks, tests, Markdown
  formatting, and workflow/security checks.

The API server runtime requires Windows with MetaTrader 5 installed and logged
in. Non-Windows systems are suitable for editing docs and most mocked tests.

## Coding Style & Naming Conventions

Target Python 3.11+. Use Ruff formatting with an 88-character line length and
Google-style docstrings. Keep type annotations complete; Pyright runs in strict
mode. Use `snake_case` for functions, variables, and modules; `PascalCase` for
classes and Pydantic models; and uppercase names for constants.

## Testing Guidelines

Pytest discovers `tests/test_*.py`, `*_test.py`, `Test*` classes, and `test_*`
functions. Coverage is branch-aware and configured to fail below 100%, so add or
adjust focused tests with each behavior change. Parametrize unit tests with
`pytest.mark.parametrize` when the same behavior should be verified across
multiple input and expected-output cases. Prefer mocked MT5/pdmt5 interactions
unless a test explicitly requires a Windows MT5 terminal.

## Design Principles

Apply KISS, DRY, and YAGNI when changing code. Prefer the simplest direct
implementation that satisfies the current requirement. Remove duplication when
it improves clarity or prevents drift, but avoid abstractions that do not serve
an immediate need. Keep changes small, focused, and easy to review.

## Commit & Pull Request Guidelines

History uses short imperative subjects and occasional Conventional Commit
prefixes, for example `refactor: delegate MT5 constant parsing...` or
`Add checks and statuses read permissions...`. Keep commits scoped to one
logical change. Before committing or opening a PR, run
`.agents/skills/local-qa/scripts/qa.sh`. Pull requests should describe the
behavior change, list verification commands, link related issues when
applicable, and call out any runtime impact for Windows/MT5 users.

## Security & Configuration Tips

Do not commit credentials, terminal account details, or real API keys. Configure
runtime values through environment variables such as `MT5API_SECRET_KEY`,
`MT5API_ROUTER_PREFIX`, `MT5API_HOST`, `MT5API_PORT`, and
`MT5API_LOG_LEVEL`.
