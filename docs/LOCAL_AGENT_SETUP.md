# Local Agent Setup

Use local PC/Mac first. No VPS yet.

## What Exists Now

- `SOUL.md` = long-term lessons
- `AGENT_RULES.md` = global guardrails
- `TRADE_LESSONS.md` = trading mistakes and fixes
- `agents/gloc/agent_manifest.json` = agent registry
- `agents/gloc/queue/` = local task queue
- `agents/gloc/prompts/` = per-agent prompts
- `mt5_planner agent-*` commands = local agent runtime

## Start Order

1. Run MT5 exporter / BTC live.
2. Run dashboard if needed.
3. Use local agent commands:

```powershell
python -m mt5_planner agent-status
python -m mt5_planner agent-enqueue --agent rloc --action report --note "check BTC"
python -m mt5_planner agent-run-once --agent rloc
```

Mac/Linux:

```bash
python -m mt5_planner agent-status
python -m mt5_planner agent-enqueue --agent rloc --action report --note "check BTC"
python -m mt5_planner agent-run-once --agent rloc
```

Shortcut scripts:

```powershell
powershell -ExecutionPolicy Bypass -File START_LOCAL_AGENTS.ps1 -Action status
powershell -ExecutionPolicy Bypass -File START_LOCAL_AGENTS.ps1 -Action enqueue-report
powershell -ExecutionPolicy Bypass -File START_LOCAL_AGENTS.ps1 -Action run-rloc
```

```bash
./start_local_agents.sh status
./start_local_agents.sh enqueue-report
./start_local_agents.sh run-rloc
```

Run a worker loop:

```powershell
powershell -ExecutionPolicy Bypass -File START_LOCAL_AGENTS.ps1 -Action loop-rloc
powershell -ExecutionPolicy Bypass -File START_LOCAL_AGENTS.ps1 -Action loop-oloc
```

```bash
./start_local_agents.sh loop-rloc
./start_local_agents.sh loop-oloc
```

Loop meaning:

- Rloc watches the queue every 30 seconds.
- Oloc watches the queue every 60 seconds.
- Stop with `Ctrl+C`.

## Windows Task Scheduler

Meaning: Windows starts the worker loops for you when you log in. No manual terminal needed.

Install:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\install_windows_tasks.ps1
```

Check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\status_windows_tasks.ps1
```

Remove:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\uninstall_windows_tasks.ps1
```

VSCode tasks:

```text
10 Gloc Scheduler Status
11 Gloc Install Scheduler
12 Gloc Uninstall Scheduler
```

Logs:

```text
agents/gloc/logs/scheduler/
```

Registered tasks:

```text
Gloc Rloc Loop
Gloc Oloc Loop
```

If Task Scheduler registration is blocked by Windows permissions, use Startup Agents instead.

Install Startup Agents:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\install_startup_agents.ps1
```

Check Startup Agents:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\status_startup_agents.ps1
```

Remove Startup Agents:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scheduler\uninstall_startup_agents.ps1
```

VSCode tasks:

```text
13 Gloc Startup Agents Status
14 Gloc Install Startup Agents
15 Gloc Uninstall Startup Agents
```

Startup Agents use hidden `.vbs` launchers in the Windows Startup folder.

## OpenClaw

OpenClaw is optional for screen control. Gloc does not need it yet because the project already has CSV, journal, reports, Discord, and scripts.

Install can take long because it may download Node/Python packages, browser binaries, Playwright/Chromium, and build native dependencies.
