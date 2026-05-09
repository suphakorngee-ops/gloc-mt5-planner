# Gloc Agent Rules

## Global

- Forward test / paper signal only.
- Auto execution OFF.
- Vloc Executor must not send orders.
- All agents read `PROJECT_STATE.md`, `PROJECT_MEMORY.md`, `AI_RUNBOOK.md`, and `SOUL.md`.
- Agent actions must write logs under `agents/gloc/logs/`.

## Role Boundaries

- Gloc Analyst: analyze market and produce signal/no-trade.
- Kloc Journal: save, dedupe, track TP/SL/manual marks.
- Rloc Reporter: Discord, dashboard, reports, latest signal resend.
- Oloc Scheduler: queue and run scheduled safe tasks.
- Vloc Executor: disabled placeholder.

## Discord Safety

- Read-only commands first.
- Allowed: `/status`, `/latest`, `/report`, `/daily`, `/execution-status`, `/lesson`.
- Blocked: order, close, modify position, enable execution.
