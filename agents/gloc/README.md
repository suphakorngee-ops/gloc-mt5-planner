# Gloc Agent System

This folder documents the local agent roles for Gloc MT5 Planner.

```text
Gloc Analyst   = reads chart/CSV and creates a signal or NO TRADE
Vloc Executor  = the only BTC demo order gateway; XAU remains OFF
Kloc Journal   = records signals, paper results, manual marks, and lessons
Rloc Reporter  = Discord, reports, dashboard, backup, order ledger summaries
Oloc Scheduler = wakes local reporting/backup/status jobs
```

## Current Status

```text
Gloc Analyst   = active
Vloc Executor  = BTC demo auto ON with guards / XAU OFF
Kloc Journal   = active
Rloc Reporter  = active through reports, dashboard, Discord routes, backups
Oloc Scheduler = local task/startup helper, not a full server bot yet
```

## Safety Rules

- Vloc is the only allowed order gateway.
- Do not add a second order sender.
- BTC demo auto must keep `demo_only`, `max_open_trades`, daily loss, duplicate, and emergency guards.
- XAU execution stays OFF unless the user explicitly asks.
- Discord chat/Q&A must stay read-only; no order commands.
- Actual MT5 order P/L belongs in the order ledger, not the paper signal journal.

## Read Next

```text
PROJECT_STATE.md
PROJECT_MEMORY.md
AI_RUNBOOK.md
AGENT_ARCHITECTURE.md
docs/DISCORD_CHANNEL_SETUP.md
```

Rloc Reporter can send routed Discord messages to `signals`, `reports`, `ops`, and `chat`. The prepared Discord bot router is read-only and answers status/report/daily/latest/execution-status/orders from local files, journals, and the MT5 order ledger.
