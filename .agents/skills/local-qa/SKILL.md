---
name: local-qa
description: Run local QA including formatting, linting, and testing for the repository. Use whenever any file has been updated.
---

# Local QA (format, lint, and test)

Run `scripts/qa.sh` relative to this skill's directory, not the shell's current working directory. The script changes to the repository root itself. It formats and fixes files in place, so check `git status` afterward.

After the run, summarize the outcome: success or failure, major warnings, and any files modified.

## When something fails

- **Missing tooling** (`command not found` or equivalent): install the tool, preferring the project's package manager (`uv`, `pnpm`), then a system package manager, then a language-specific installer (`pipx`, `npm`, `go install`). Rerun `scripts/qa.sh` and repeat until QA completes. If installation fails or needs privileges you lack, report what was attempted and the exact failure, then stop.
- **Any other failure**: fix the root cause and rerun until QA passes or you hit a blocker. Do not bypass or weaken checks, because the script is the repository's quality gate.

Run only commands needed for QA, fixes, and tool installation.
