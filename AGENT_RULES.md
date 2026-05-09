# Gloc Agent Rules

## Global

- BTC demo auto execution may run only through Vloc Executor.
- XAU execution remains OFF.
- No agent other than Vloc may send orders.
- All agents read `PROJECT_STATE.md`, `PROJECT_MEMORY.md`, `AI_RUNBOOK.md`, and `SOUL.md`.
- Agent actions must write logs under `agents/gloc/logs/`.

## Role Boundaries

- Gloc Analyst: analyze market and produce signal/no-trade.
- Kloc Journal: save, dedupe, track TP/SL/manual marks.
- Rloc Reporter: Discord, dashboard, reports, latest signal resend.
- Oloc Scheduler: queue and run scheduled safe tasks.
- Vloc Executor: BTC demo order gateway with guards.

## Discord Safety

- Read-only commands first.
- Allowed: `/status`, `/latest`, `/report`, `/daily`, `/execution-status`, `/lesson`.
- Blocked in Discord chat: order, close, modify position, enable execution.
