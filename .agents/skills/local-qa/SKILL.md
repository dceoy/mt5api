---
name: local-qa
description: Run local QA including formatting, linting, and testing for the repository. Use whenever any file has been updated.
---

# Local QA (format, lint, and test)

Run `scripts/qa.sh` relative to this skill's directory, not the shell's current working directory. The script changes to the repository root itself.

## Procedure

- Execute `scripts/qa.sh` from the skill directory when this skill is triggered (it formats and fixes files in place, so check `git status` afterward).
- Capture and summarize key output (success/failure, major warnings, and any files modified).
- If the script fails due to missing tooling (`command not found`, missing executable, or equivalent), install the missing tool(s) and rerun `scripts/qa.sh` from the skill directory.
- Install tools using this order of preference:
  1. Use the project's package manager when applicable (`uv`/`poetry` for Python, package manager scripts/dependencies for Node.js).
  2. Use a system package manager (`brew` on macOS, `apt` on Debian/Ubuntu) when project-local install is not applicable.
  3. Use language-specific installers as fallback (`pipx`/`pip`, `npm`, `go install`, etc.).
- If multiple tools are missing, repeat install -> rerun until QA completes or you hit a blocker.
- If installation fails or requires unavailable privileges, report what was attempted, the exact failure, and stop.
- If QA fails for another reason, fix the root cause and rerun until QA passes or a blocker is reached. Do not bypass or weaken checks.
- Do not run unrelated commands; only run commands needed for QA, fixes, and missing-tool installation.
