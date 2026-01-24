# Repository Guidelines

## Commands

### Development Setup

```bash
# Install dependencies with uv (modern Python package manager)
uv sync
```

### Code Quality and Testing

**IMPORTANT: Run these checks on every code change before committing.**

```bash
# Run all quality checks (formatting, linting, type checking, tests)
uv run ruff format . && uv run ruff check --fix . && uv run pyright . && uv run pytest tests/ -v

# Individual commands (if needed):
uv run ruff format .        # Format code
uv run ruff check --fix .   # Lint code
uv run pyright .            # Type check
uv run pytest tests/ -v     # Run tests only
```

### Documentation

**IMPORTANT: Update documentation after any public API changes.**

```bash
uv run mkdocs build         # Build documentation with MkDocs
uv run mkdocs serve         # Serve documentation locally with live reload
uv run mkdocs gh-deploy     # Deploy documentation to GitHub Pages
```

## Commit & Pull Request Guidelines

- Commit messages are short, imperative, sentence-case.
- Branch names use appropriate prefixes on creation (e.g., `feature/short-description`, `bugfix/short-description`).
- PRs should include: a clear summary, relevant context or linked issue.
- When instructed to create a PR, create it as a draft with appropriate labels by default.

## Architecture

### Project Overview

- **Purpose**: Pandas-based data handler for MetaTrader 5 trading platform
- **Target Platform**: Windows only (MetaTrader5 API requirement)
- **Domain**: Financial/trading data analysis
- **Status**: Early development (Beta)

### Key Dependencies

- **MetaTrader5**: Windows-only trading platform API for market data
- **pandas**: Core data manipulation and analysis
- **pydantic**: Data validation and serialization for financial data models

### Package Structure

- `pdmt5/`: Main package directory
  - `__init__.py`: Package initialization and exports (Mt5Client, Mt5Config, Mt5DataClient, Mt5RuntimeError, Mt5TradingClient)
  - `mt5.py`: MT5 terminal client with context manager support (`Mt5Client`, `Mt5RuntimeError`)
  - `dataframe.py`: MT5 data client with pandas DataFrame conversion (`Mt5Config`, `Mt5DataClient`)
  - `trading.py`: Trading operations client (`Mt5TradingClient`, `Mt5TradingError`)
  - `utils.py`: Utility decorators and functions for time conversion and DataFrame indexing
- `tests/`: Comprehensive test suite (pytest-based)
  - `test_init.py`, `test_mt5.py`, `test_dataframe.py`, `test_trading.py`, `test_utils.py`
- `docs/`: MkDocs documentation with API reference
  - `docs/api/`: Auto-generated API documentation for all modules
- Modern Python packaging with `pyproject.toml` and uv dependency management

### Development Tools Configuration

- **Ruff**: Comprehensive linting with 40+ rule categories enabled
- **Pyright**: Strict type checking mode
- **pytest**: Testing with coverage reporting (branch coverage enabled)
- **Google-style docstrings**: Documentation convention
- **Line length**: 88 characters

### Quality Standards

- Type hints required (pyright strict mode)
- Comprehensive linting with 35+ rule categories (ruff)
- Test coverage tracking with 100% (pytest-cov)
- Parametrized tests for input/result matrices using `pytest.mark.parametrize` (pytest)
- Professional financial software standards
- Pydantic models for data validation and configuration
- Context manager support for resource management

### Test Desiderata

Desirable properties of tests:

- **Isolated**: results never depend on test order or shared state.
- **Composable**: validate dimensions separately and combine results.
- **Deterministic**: same inputs produce the same outcome.
- **Fast**: keep runtime short to encourage frequent execution.
- **Writable**: cheap to create relative to code value.
- **Readable**: intent and motivation are obvious to reviewers.
- **Behavioral**: sensitive to user-visible behavior changes.
- **Structure-insensitive**: refactors shouldn’t flip results.
- **Automated**: run without human intervention.
- **Specific**: failures point clearly to the cause.
- **Predictive**: passing suite signals production readiness.
- **Inspiring**: green builds build team confidence.

## Documentation with MkDocs

Uses MkDocs with Material theme for API documentation built from Google-style docstrings.

### Structure

- `docs/index.md`: Main documentation
- `docs/api/`: Auto-generated API reference
  - `mt5.md`: Mt5Client and Mt5RuntimeError
  - `dataframe.md`: Mt5Config and Mt5DataClient
  - `trading.md`: Mt5TradingClient and Mt5TradingError
  - `utils.md`: Utility decorators and helper functions

### Workflow

1. Add Google-style docstrings to functions/classes
2. Local preview: `uv run mkdocs serve`
3. Build: `uv run mkdocs build`
4. Deploy: `uv run mkdocs gh-deploy`

## Code Design Principles

Follow Robert C. Martin's SOLID and Clean Code principles:

### SOLID Principles

1. **SRP (Single Responsibility)**: One reason to change per class; separate concerns (e.g., storage vs formatting vs calculation)
2. **OCP (Open/Closed)**: Open for extension, closed for modification; use polymorphism over if/else chains
3. **LSP (Liskov Substitution)**: Subtypes must be substitutable for base types without breaking expectations
4. **ISP (Interface Segregation)**: Many specific interfaces over one general; no forced unused dependencies
5. **DIP (Dependency Inversion)**: Depend on abstractions, not concretions; inject dependencies

### Clean Code Practices

- **Naming**: Intention-revealing, pronounceable, searchable names (`daysSinceLastUpdate` not `d`)
- **Functions**: Small, single-task, verb names, 0-3 args, extract complex logic
- **Classes**: Follow SRP, high cohesion, descriptive names
- **Error Handling**: Exceptions over error codes, no null returns, provide context, try-catch-finally first
- **Testing**: TDD, one assertion/test, FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely), Arrange-Act-Assert pattern
- **Code Organization**: Variables near usage, instance vars at top, public then private functions, conceptual affinity
- **Comments**: Self-documenting code preferred, explain "why" not "what", delete commented code
- **Formatting**: Consistent, vertical separation, 88-char limit, team rules override preferences
- **General**: DRY, KISS, YAGNI, Boy Scout Rule, fail fast

## Development Methodology

Follow Martin Fowler's Refactoring, Kent Beck's Tidy Code, and t_wada's TDD principles:

### Core Philosophy

- **Small, safe changes**: Tiny, reversible, testable modifications
- **Separate concerns**: Never mix features with refactoring
- **Test-driven**: Tests provide safety and drive design
- **Economic**: Only refactor when it aids immediate work

### TDD Cycle

1. **Red** → Write failing test
2. **Green** → Minimum code to pass
3. **Refactor** → Clean without changing behavior
4. **Commit** → Separate commits for features vs refactoring

### Practices

- **Before**: Create TODOs, ensure coverage, identify code smells
- **During**: Test-first, small steps, frequent tests, two hats rule
- **Refactoring**: Extract function/variable, rename, guard clauses, remove dead code, normalize symmetries
- **TDD Strategies**: Fake it, obvious implementation, triangulation

### When to Apply

- Rule of Three (3rd duplication)
- Preparatory (before features)
- Comprehension (as understanding grows)
- Opportunistic (daily improvements)

### Key Rules

- One assertion per test
- Separate refactoring commits
- Delete redundant tests
- Human-readable code first

> "Make the change easy, then make the easy change." - Kent Beck
