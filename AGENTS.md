# Repository Guidelines

## Build, Test, and Development Commands

- `.agents/skills/local-qa/scripts/qa.sh`: run the repository QA workflow after
  any file update. This wraps formatting, linting, type checks, tests, Markdown
  formatting, and workflow/security checks.

The API server runtime requires Windows with MetaTrader 5 installed and logged
in. Non-Windows systems are suitable for editing docs and most mocked tests.

## Testing Guidelines

Parametrize unit tests with `pytest.mark.parametrize` when the same behavior
should be verified across multiple input and expected-output cases. Prefer
mocked MT5/pdmt5 interactions unless a test explicitly requires a Windows MT5
terminal.

## Design Principles

Apply KISS, DRY, and YAGNI when changing code. Prefer the simplest direct
implementation that satisfies the current requirement. Remove duplication when
it improves clarity or prevents drift, but avoid abstractions that do not serve
an immediate need. Keep changes small, focused, and easy to review.

## Commit & Pull Request Guidelines

Keep commits scoped to one logical change. Before committing or opening a PR,
run `.agents/skills/local-qa/scripts/qa.sh`. Pull requests should describe the
behavior change, list verification commands, link related issues when
applicable, and call out any runtime impact for Windows/MT5 users.

## Security & Configuration Tips

Do not commit credentials, terminal account details, or real API keys. Configure
runtime values through environment variables such as `MT5API_SECRET_KEY`,
`MT5API_ROUTER_PREFIX`, `MT5API_HOST`, `MT5API_PORT`, and
`MT5API_LOG_LEVEL`.
