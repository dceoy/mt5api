#!/usr/bin/env bash

set -euox pipefail
cd "$(git rev-parse --show-toplevel)"

COOLDOWN_DAYS=7
export UV_EXCLUDE_NEWER="${COOLDOWN_DAYS} days"
export NPM_CONFIG_MIN_RELEASE_AGE="${COOLDOWN_DAYS}"
export PNPM_CONFIG_MINIMUM_RELEASE_AGE=$((COOLDOWN_DAYS * 24 * 60))

# Python
uv sync
uv run ruff format .
uv run ruff check --fix .
uv run pyright .
uv run pytest

# Markdown
npx -y prettier --write './**/*.md'

# GitHub Actions
case "${OSTYPE}" in
  darwin* | linux* )
    uvx zizmor --fix=safe .github/workflows
    git ls-files -z -- '.github/workflows/*.yml' | xargs -0 -t actionlint
    git ls-files -z -- '.github/workflows/*.yml' | xargs -0 -t uvx yamllint -d '{"extends": "relaxed", "rules": {"line-length": "disable"}}'
    uvx checkov --framework=all --output=github_failed_only --directory=.
    ;;
  * )
    echo "GitHub Actions linting is only supported on Linux and macOS."
    ;;
esac
