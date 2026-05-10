# Gloc MT5 Planner

Local-first MT5 trading planner for BTCUSDm and XAUUSDm on M5.

Gloc is built to read MT5 chart data, create guarded trade plans, journal every signal, report results, send Discord alerts, and run BTC demo execution through one controlled gateway.

## Current Mode

- BTCUSDm M5: demo auto execution is enabled.
- XAUUSDm M5: demo auto execution is enabled for weekday gold sessions.
- Fixed lot: `0.01`.
- BTC execution is demo-only and must pass Vloc guards.
- GitHub is used for private source backup, not for secrets or live trading data.

## Main Flow

```text
MT5 EA exporter
-> CSV in MQL5/Files
-> VS Code task / PowerShell runner
-> Gloc BTC Live Planner
-> Journal SQLite
-> Forward report / daily report / dashboard
-> Discord signal/report/ops alerts
-> Vloc Demo Executor for BTC only
```

## Safety Rules

- Only Vloc may send orders.
- BTC/XAU orders are demo-only.
- BTC and XAU each have their own `max_open_trades = 1`, so they can each hold one Vloc position at the same time.
- No Discord chat command may send, close, or modify an order.
- Webhooks, journals, live CSV files, logs, reports, backups, and guard files stay local only.

## BTC Demo Execution Guards

BTC demo auto execution uses `mt5_planner/demo_executor.py`.

Current BTC config:

```text
enabled: true
mode: demo_auto
dry_run: false
demo_only: true
fixed_lot: 0.01
max_open_trades: 1
daily_max_loss_usd: 5
duplicate_guard: true
emergency_stop: true
manage_positions: true
move_be_at_rr: 1.0
partial_close_ratio: 0.5
```

The executor checks:

- MT5 account trade mode is demo.
- Daily lock is not active.
- Duplicate signal has not already been seen.
- Risk guard passes.
- Lot size is valid.
- Open position count is below the limit.
- Discord ops alert is sent after sent/reject/error.

## BTC Order Manager

Vloc also manages BTC demo positions opened by Gloc's magic number.

At `+1R`:

- If volume is large enough, it attempts a partial close.
- With fixed lot `0.01`, partial close is normally skipped because it is already the minimum lot.
- It then moves SL to break-even.
- Every action/reject/error is logged to `reports/manager.log` and sent to Discord ops.

## Current Forward Status

As of the latest saved state:

```text
BTC signals: 34
BTC trade ideas: 6 grouped from 34 raw signals
BTC idea result: wins 5 | losses 1 | open 0
BTC closed WR: 83.3%
BTC PF: 5.14
BTC expectancy: +0.853R/signal

XAU signals: 0
XAU execution: OFF
```

These numbers are forward-test data and can change as more signals are collected.

## Run In VS Code

Use `Terminal > Run Task...`.

```text
LIVE 01 / BTC Demo Auto              run BTC planner and BTC demo executor
LIVE 02 / XAU Weekdays               run XAU planner only when gold market is open
OPS 00 / Health Check                one-page MT5/CSV/Discord/order-ledger status
EXEC 01 / Status All                 confirm BTC/XAU execution state
EXEC 02 / BTC Manage Position        run BTC order manager once
EXEC 03 / BTC Dry Run                validate latest BTC signal without order
EXEC 04 / Order Ledger All           sync and report actual MT5 orders
REPORT 01 / Forward All              forward report
REPORT 02 / Daily All                daily summary
OPS 01 / Safe Automation             report, daily, state, backup, Discord digest
DISCORD 01 / Resend Latest Signal    resend latest Discord signal
DISCORD 02 / Bot Run                 run Discord Q&A bot when token is configured
DASH 01 / Live View                  live dashboard server
DASH 02 / Open Static                static dashboard file
```

## Run By PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action live
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action live
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action health
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action execution
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action execution-dry-run
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action execution-manage
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action order-report
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action report
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol all -Action safe-automation
```

## Market Notes

- BTC can run on weekends if the broker feed is active.
- XAU is normally closed on Saturday/Sunday, so XAU live/execution should stay inactive during gold market closure.
- If MT5 or the EA exporter is not running, Gloc can only use the last local CSV copy.

## Discord

Recommended Discord channels:

```text
#gloc-signals
#gloc-reports
#gloc-ops
#gloc-chat
```

Webhook route support:

```text
signals -> MT5_PLANNER_DISCORD_SIGNALS_WEBHOOK
reports -> MT5_PLANNER_DISCORD_REPORTS_WEBHOOK
ops     -> MT5_PLANNER_DISCORD_OPS_WEBHOOK
chat    -> MT5_PLANNER_DISCORD_CHAT_WEBHOOK
fallback -> MT5_PLANNER_DISCORD_WEBHOOK
```

Secrets must stay in `DISCORD_WEBHOOK.local.ps1` or local environment variables. Do not commit them.

Test a route:

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action test-discord -DiscordRoute signals
```

## Important Files

```text
PROJECT_STATE.md        latest saved state
PROJECT_MEMORY.md       long-term project memory
AI_RUNBOOK.md           continuation instructions for Codex
USER_PLAYBOOK.md        day-to-day user guide
AGENT_RULES.md          agent safety rules
TRADE_LESSONS.md        lessons from signals and mistakes
docs/                   setup notes and supporting docs
config_btc.json         BTC demo config
config.json             XAU demo config
mt5_planner/            source code
agents/gloc/            local agent definitions
```

## GitHub Pro Use

This repo is pushed to private GitHub as source backup and version history.

Do commit:

- Source code
- Docs
- VS Code tasks
- Config templates and safe configs

Do not commit:

- Discord webhooks
- API keys or tokens
- SQLite journals
- MT5 CSV exports
- Reports/logs/backups
- Guard runtime files

## Install

Use the project Python environment or install requirements:

```powershell
py -m pip install -r requirements.txt
```

For the Discord bot:

```powershell
py -m pip install -r requirements-discord-bot.txt
```

## MT5 Exporter

If direct MetaTrader5 Python access is unavailable, use the EA exporter:

```text
mt5_exporter/ChartDataExporter.mq5
mt5_exporter/ChartDataExporter_BTCUSDm.mq5
```

Attach the EA to the correct MT5 chart and export:

```text
BTCUSDm M5 -> btcusdm_m5.csv
XAUUSDm M5 -> xauusdm_m5.csv
```

## Development Rule

Do not create a second execution path. Any future order send must go through Vloc / `mt5_planner/demo_executor.py`; any future close, modify, TP1, or break-even action must go through `mt5_planner/trade_manager.py`.
