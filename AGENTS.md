# Repository Guidelines

## Commands

### Development Setup

- `uv sync --dev` installs runtime and development dependencies.
- `uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000` starts the API locally.
- `uv run python -m mt5api` starts the app using `MT5API_HOST`, `MT5API_PORT`, and `MT5API_LOG_LEVEL`.
- `uv run mkdocs serve` previews the documentation site.

### Code Quality and Documentation

**Important**: Run these before committing or creating a PR.

1. **Format, lint, and test**: Use `local-qa` skill.
2. **Documentation build**: Run `uv run mkdocs build` when documentation, configuration, or OpenAPI-visible behavior changes.

## Architecture

### Runtime Constraints

- The API server must run on Windows with a logged-in MetaTrader 5 terminal.
- Linux and macOS are for HTTP clients, documentation work, and local non-runtime development only.

### Key Dependencies

- `pdmt5`: Underlying MetaTrader 5 client integration used by the API layer.
- `fastapi`: HTTP application framework and OpenAPI generation.

### Package Structure

- `mt5api/`: Main FastAPI package.
  - `main.py`: App wiring, lifespan handling, middleware, and router registration.
  - `__main__.py`: CLI entry point for launching the API from environment-backed configuration.
  - `config.py`: Environment-backed configuration normalization and validation.
  - `auth.py`: Optional API key authentication helpers.
  - `dependencies.py`: Shared endpoint dependencies and MT5 accessors.
  - `formatters.py`: JSON and Parquet response formatting helpers.
  - `models.py`: Pydantic API models.
  - `middleware.py`: Request logging and error handling.
  - `constants.py`: Shared constants and environment variable names.
  - `routers/`: Endpoint groups for operations: `health.py`, `symbols.py`, `market.py`, `account.py`, `history.py`, `calc.py`, and `trading.py`.
- `tests/`: Pytest suite covering API behavior, configuration, middleware, and CLI entry points.
- `docs/`: MkDocs documentation, including REST API and deployment guidance.

## Quality Standards

- Type hints required (pyright strict mode)
- Comprehensive linting with 35+ rule categories (ruff)
- Test coverage tracking with 100% (pytest-cov)
- Parametrized tests for input/result matrices using `pytest.mark.parametrize` (pytest)
- Test doubles (mocks, stubs) using `pytest_mock` for external dependencies (pytest-mock)
- Pydantic models for data validation and configuration

## Documentation Workflow

1. Update docstrings and docs when behavior, configuration, or OpenAPI-visible output changes.
2. Local preview: `uv run mkdocs serve`
3. Build validation: `uv run mkdocs build`

## Commit & Pull Request Guidelines

- Run QA using `local-qa` skill before committing or creating a PR.
- Branch names use appropriate prefixes on creation (e.g., `feature/...`, `bugfix/...`, `refactor/...`, `docs/...`, `chore/...`).
- When instructed to create a PR, create it as a draft with appropriate labels by default.

## Security & Configuration Tips

- Do not commit real MT5 credentials or API keys.
- Configure `MT5API_SECRET_KEY`, `MT5API_ROUTER_PREFIX`, and `MT5API_LOG_LEVEL` through environment variables.
- Keep runtime configuration in the environment instead of hardcoding deployment values.
- Authentication mode is fixed at process startup; cover both authenticated and unauthenticated behavior when changing auth-related code.

## Code Design Principles

Always prefer the simplest design that works.

- **KISS**: Choose straightforward solutions and avoid unnecessary abstraction.
- **DRY**: Remove duplication when it improves clarity and maintainability.
- **YAGNI**: Do not add features, hooks, or flexibility until they are needed.
- **SOLID/Clean Code**: Apply these as tools only when they keep the design simpler and easier to change.

## Development Methodology

Keep delivery incremental, test-backed, and easy to review.

- Make small, safe, reversible changes.
- Prefer `Red -> Green -> Refactor`.
- Do not mix feature work and refactoring in the same commit.
- Refactor when it improves clarity or removes real duplication (Rule of Three).
- Keep tests fast, focused, and self-validating.
