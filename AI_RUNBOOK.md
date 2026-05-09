# MT5 Planner AI Runbook

คู่มือนี้สำหรับ AI/แชทใหม่ ใช้ทำงานต่อโดยไม่เริ่มใหม่

## Always Read First

1. `PROJECT_MEMORY.md`
2. `USER_PLAYBOOK.md`
3. current configs:
   - `config.json`
   - `config_btc.json`
   - `config_xau_cent.json`
   - `config_btc_cent.json`

## Current State

- Product is local/free MT5 planner.
- No auto execution.
- Live mode is forward test / paper signal.
- Logic currently uses structure/SMC style direction, not EMA gate.
- Fixed lot is `0.01`.
- Current journal files are clean:
  - `journal_xau_current.sqlite`
  - `journal_btc_current.sqlite`
  - `journal_xau_cent.sqlite`
  - `journal_btc_cent.sqlite`

## Main User Tasks

Current visible VSCode tasks:

```text
01 Gloc BTC Live
02 Gloc XAU Live Weekdays
03 Gloc Dashboard Live
04 Gloc Safe Automation
05 Gloc Report All
06 Gloc Daily Summary All
07 Gloc Execution Status
08 Gloc Dashboard Open
```

XAUUSD/gold is normally closed on Saturday and Sunday. During weekends, prefer BTC forward testing and reports. Do not run XAU live expecting new market data while gold is closed.

Use VSCode tasks:

```text
MAIN BTC Live
MAIN BTC Report
MAIN BTC Daily Summary
MAIN BTC Backtest+Analyze

MAIN XAU Live
MAIN XAU Report
MAIN XAU Daily Summary
MAIN XAU Backtest+Analyze
```

Use script directly:

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action live
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Action report
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action live
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Action report
```

Cent mode:

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Account cent -Action live
```

## Do Not Do Yet

- Do not enable auto order execution.
- Do not add more entry logic while collecting forward signals unless user explicitly asks.
- Do not delete old journals.
- Do not merge old journal data into current reports.

## Next Useful Work While Signals Are Collected

Good:

- alert on new signal
- reports saved to `reports/`
- lightweight dashboard from journal
- risk preset UI/config
- auto execution skeleton with disabled flag

Avoid:

- overfitting setup allowlists before 50-100 forward signals
- changing strategy after every few signals

## Auto Execution Gate

Only discuss execution after:

```text
50-100 current forward signals
positive expectancy
profit factor > 1.3
daily max loss implemented
max open trades implemented
duplicate order guard implemented
demo/cent only flag implemented
```

## Implemented Non-Logic Utilities

- Alerts:
  - `mt5_planner/alerts.py`
  - writes `reports/alerts.log`
  - writes `reports/latest_signal.txt`
  - beeps/prints on new saved signal
- Daily reports:
  - command `daily-report`
  - `MT5_PLANNER.ps1 -Action daily`
  - saves `reports/daily_btc.txt` or `reports/daily_xau.txt`
- Dashboard:
  - command `dashboard`
  - output `reports/dashboard.html`
- Execution skeleton:
  - `mt5_planner/execution.py`
  - command `execution-status`
  - configs keep `execution.enabled = false`

## Implemented Journal/Backup Utilities

- Manual trade journal:
  - columns added to `signals`: `manual_status`, `manual_entry`, `manual_exit`, `manual_note`, `manual_updated_at`
  - commands: `manual-list`, `manual-mark`
  - VSCode tasks: `08 MAIN BTC Manual List`, `09 MAIN XAU Manual List`
- Backup:
  - module `mt5_planner/backup.py`
  - command `backup`
  - VSCode task `07 MAIN Backup`
- Dashboard:
  - auto-refresh meta tag every 15 seconds
  - includes manual status column
  - live server command `dashboard-serve`
  - task `07 MAIN Dashboard Live Server`
  - local URL `http://127.0.0.1:8765`
  - live page supports taken/skipped/missed/watch buttons via `/api/mark`
- Execution guards:
  - daily lock files under `guards/<symbol>_<YYYY-MM-DD>.lock`
  - duplicate seen file paths under `guards/<symbol>_seen_signals.json`
  - commands: `execution-lock`, `execution-unlock`, `execution-status`
- Project state saver:
  - module `mt5_planner/project_state.py`
  - command `save-state`
  - task `09 MAIN Save Project State`
  - output `PROJECT_STATE.md`
- Discord alert:
  - configured under `alerts.discord`
  - default `enabled=false`
  - can read webhook from env `MT5_PLANNER_DISCORD_WEBHOOK`
  - setup docs: `DISCORD_ALERT_SETUP.md`
- Safe automation:
  - command `safe-automation`
  - VSCode task `11 MAIN Safe Automation + Discord Digest`
  - writes forward/daily reports, saves `PROJECT_STATE.md`, runs backup, and can send Discord digest
  - never sends orders and keeps execution OFF
- Forward duplicate control:
  - `Journal.save_signal` stores `idea_key`
  - `attach_context` builds `idea_key` and `duplicate_window_seconds`
  - repeated same idea inside the valid window is skipped
  - forward report displays grouped `trade ideas` alongside raw signals
- Discord bot preparation:
  - module `mt5_planner/discord_bot.py`
  - command `discord-reply`
  - VSCode task `12 MAIN Discord Bot Dry Reply`
  - supports read-only `/status`, `/report`, `/daily`, `/latest`, `/execution-status`
- Signal alert recovery:
  - `reports/alerts.log` stores every alert line
  - `reports/latest_signal.txt` stores the latest saved signal
  - `reports/signal_inbox.txt` stores a persistent inbox of new saved signals
  - command `resend-latest` and task `09 Gloc Resend Latest Signal` resend latest signal to Discord
  - Discord format is compact with emoji icons and always says paper/manual only, auto execution OFF
  - Discord route support: signals/reports/ops webhooks with fallback to `MT5_PLANNER_DISCORD_WEBHOOK`
  - setup docs: `DISCORD_CHANNEL_SETUP.md`
- Agent architecture docs:
  - `AGENT_ARCHITECTURE.md`
  - five-agent model: Gloc Analyst, Vloc Executor, Kloc Journal, Rloc Reporter, Oloc Scheduler

## Gloc Agent Names

Use these names consistently:

```text
Gloc Analyst   = วิเคราะห์กราฟ / ออก signal หรือ NO TRADE
Vloc Executor  = ส่ง order ในอนาคต ตอนนี้ OFF
Kloc Journal   = บันทึก signal, TP/SL, taken/skipped
Rloc Reporter  = Discord, dashboard, report, backup
Oloc Scheduler = ปลุกงานรายรอบ เช่น save-state/report
```

Agent docs:

```text
agents/gloc/README.md
agents/gloc/gloc_analyst.md
agents/gloc/vloc_executor.md
agents/gloc/kloc_journal.md
agents/gloc/rloc_reporter.md
agents/gloc/oloc_scheduler.md
```

## New Chat Handoff

If token/context runs out, ask the next chat:

```text
อ่าน PROJECT_STATE.md, PROJECT_MEMORY.md, AI_RUNBOOK.md และ agents/gloc/README.md แล้วทำต่อจากโปรเจกต์ Gloc MT5 Planner ห้ามเริ่มใหม่ ห้ามเปิด auto execution
```

Before starting a new chat, run this VSCode task if possible:

```text
09 MAIN Save Project State
```

## Discord Future

Current Discord integration is webhook-only, so it sends alerts out but cannot read user messages.

To let the user type questions in Discord and get answers, build a Discord Bot service later:

```text
Discord command -> Rloc Reporter bot -> read journal/report/state -> reply in Discord
```

Suggested read-only commands first:

```text
/status
/signals btc
/signals xau
/report
/daily
/save-state
```

BTC demo auto execution is now implemented through `mt5_planner/demo_executor.py`.
Vloc Executor is the only order gateway.

Current execution state:

```text
BTC demo: enabled=true, dry_run=false, demo_only=true, fixed lot 0.01
XAU demo: enabled=false, dry_run=true
```

Guards:

```text
demo account check via MT5 account trade_mode
max_open_trades=1
daily_max_loss_usd=5 for BTC
duplicate seen file under guards/
daily lock file under guards/
Discord ops alert after execution/reject
BTC order manager:
- `mt5_planner/trade_manager.py`
- runs from live loop and command `execution-manage`
- manages only positions matching the configured symbol and magic number
- at +1R, attempts partial close if volume allows, then moves SL to BE
- with fixed lot 0.01, partial close usually skips and BE move is the main action
```

Do not add any second order sender. Keep order sends inside Vloc/demo_executor and position management inside trade_manager.

## Multi-Model Future

Multi-model is possible, but all models should use files as shared memory:

```text
Gemma/Gemini = summarize, clean notes, organize journal
GPT          = strategy review, coding, system decisions
Files        = shared memory and audit trail
```

Do not let multiple models send orders. Vloc Executor is the only future order gateway, and it is OFF.

## Local Agent Runtime

Local-first real agent scaffolding exists:

```text
SOUL.md
AGENT_RULES.md
TRADE_LESSONS.md
LOCAL_AGENT_SETUP.md
agents/gloc/agent_manifest.json
agents/gloc/queue/pending.jsonl
agents/gloc/queue/done.jsonl
agents/gloc/prompts/*.prompt.md
mt5_planner/agent_runtime.py
START_LOCAL_AGENTS.ps1
start_local_agents.sh
```

Commands:

```powershell
python -m mt5_planner agent-status
python -m mt5_planner agent-enqueue --agent rloc --action report --note "manual report"
python -m mt5_planner agent-run-once --agent rloc
python -m mt5_planner agent-run-loop --agent rloc --interval 30
```

Vloc remains blocked from order actions.

OpenClaw note:

- `OPENCLAW_NOTES.md` explains it.
- Do not put OpenClaw in the trading path yet.
- Current safer path is direct CSV/journal/scripts.

Windows Task Scheduler:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\install_windows_tasks.ps1
powershell -ExecutionPolicy Bypass -File scripts\scheduler\status_windows_tasks.ps1
powershell -ExecutionPolicy Bypass -File scripts\scheduler\uninstall_windows_tasks.ps1
```

It registers `Gloc Rloc Loop` and `Gloc Oloc Loop` at user logon. Logs go to `agents/gloc/logs/scheduler/`.

If Task Scheduler is denied, use Startup Agents:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\install_startup_agents.ps1
powershell -ExecutionPolicy Bypass -File scripts\scheduler\status_startup_agents.ps1
powershell -ExecutionPolicy Bypass -File scripts\scheduler\uninstall_startup_agents.ps1
```
