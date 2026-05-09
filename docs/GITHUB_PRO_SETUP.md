# GitHub Pro Setup

Purpose: use GitHub Pro as a private backup and version history for Gloc MT5 Planner.

## What Goes To GitHub

- Source code in `mt5_planner/`
- PowerShell runners and scheduler scripts
- Project docs and runbooks
- VS Code tasks
- Agent prompts/rules/manifests
- Example configs

## What Stays Local Only

- Discord webhook files
- API keys, tokens, `.env`
- MT5 live CSV exports
- SQLite journals
- Reports/logs/backups
- Python virtual environments and downloaded dependencies

## Recommended GitHub Repo Settings

- Visibility: Private
- Default branch: `main`
- Enable Dependabot alerts
- Add branch protection for `main` after the first push
- Work on branches named `codex/...`

## Safe Workflow

1. Edit locally.
2. Run compile/check tasks.
3. Commit only source/docs/config examples.
4. Push to the private repo.
5. Never commit webhook/token/journal/live market data.

## Gloc Safety Rule

GitHub is for backup and code history only. It must not enable MT5 auto execution.
