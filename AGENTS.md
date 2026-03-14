# Repository Guidelines

## Project Structure & Module Organization

- `mt5api/` contains the FastAPI application.
- `main.py` wires logging, middleware, CORS, and lifespan handling.
- `routers/` holds the read-only endpoint groups: `health.py`, `symbols.py`, `market.py`, `account.py`, and `history.py`.
- Shared logic lives in top-level modules such as `auth.py`, `dependencies.py`, `formatters.py`, and `models.py`.
- Tests live in `tests/` and follow the package layout with `test_*.py` files.
- Documentation is under `docs/` with MkDocs config in `mkdocs.yml`.

## Build, Test, and Development Commands

Use `uv` for local work:

- Before each code or documentation change, run linting,formatting, and tests using `local-qa` skill.
- `uv sync --dev` installs runtime and development dependencies.
- `uv run uvicorn mt5api.main:app --host 0.0.0.0 --port 8000` starts the API locally.
- `uv run python -m mt5api` starts the app using `API_HOST`, `API_PORT`, and `API_LOG_LEVEL`.
- `uv run mkdocs serve` previews the docs site.

## Coding Style & Naming Conventions

- Target Python 3.11+ with 4-space indentation and an 88-character line limit.
- Keep modules and functions in `snake_case`.
- Classes use `PascalCase`.
- Constants use `UPPER_SNAKE_CASE`.
- Type annotations are expected.
- Docstrings should follow the Google convention configured in Ruff.
- Keep endpoint code grouped by domain under `mt5api/routers/`.
- Parametrized tests for input/result matrices using `pytest.mark.parametrize` (pytest)

## Commit & Pull Request Guidelines

- Run QA using `local-qa` before committing or creating a PR.
- Include request/response examples or screenshots when docs or OpenAPI-visible behavior changes.
- Keep PRs focused and include: concise summary, affected workflow paths, linked issue/context, and regenerated `README.md` when workflow inventory changes.
- Branch names use appropriate prefixes on creation (e.g., `feature/...`, `bugfix/...`, `refactor/...`, `docs/...`, `chore/...`).
- When instructed to create a PR, create it as a draft with appropriate labels by default.

## Security & Configuration Tips

- Do not commit real MT5 credentials or API keys.
- Configure `MT5_API_KEY`, `API_RATE_LIMIT`, `API_CORS_ORIGINS`, and `API_LOG_LEVEL` through environment variables.
- The API server must run on Windows with a logged-in MetaTrader 5 terminal.
- Linux and macOS are for HTTP clients and local non-runtime work only.

## Code Design Principles

Always prefer the simplest design that works.

- **KISS**: Choose straightforward solutions and avoid unnecessary abstraction.
- **DRY**: Remove duplication when it improves clarity and maintainability.
- **YAGNI**: Do not add features, hooks, or flexibility until they are needed.
- **SOLID/Clean Code**: Apply these as tools, only when they keep the design simpler and easier to change.

## Development Methodology

Keep delivery incremental, test-backed, and easy to review.

- Make small, safe, reversible changes.
- Prefer `Red -> Green -> Refactor`.
- Do not mix feature work and refactoring in the same commit.
- Refactor when it improves clarity or removes real duplication (Rule of Three).
- Keep tests fast, focused, and self-validating.
