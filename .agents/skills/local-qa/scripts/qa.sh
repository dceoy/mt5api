#!/usr/bin/env bash

set -euox pipefail
cd "$(git rev-parse --show-toplevel)"

# Python
uv run ruff format .
uv run ruff check --fix .
uv run pyright .
uv run pytest

# Markdown
npx -y prettier --write './**/*.md'

# GitHub Actions
case "${OSTYPE}" in
  darwin* | linux* )
    zizmor --fix=safe .github/workflows
    git ls-files -z -- '.github/workflows/*.yml' | xargs -0 -t actionlint
    git ls-files -z -- '.github/workflows/*.yml' | xargs -0 -t yamllint -d '{"extends": "relaxed", "rules": {"line-length": "disable"}}'
    checkov --framework=all --output=github_failed_only --directory=.
    ;;
  * )
    echo "GitHub Actions linting is only supported on Linux and macOS."
    ;;
esac
