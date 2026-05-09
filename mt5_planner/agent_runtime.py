from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time

from .automation import run_safe_automation
from .backup import run_backup
from .daily_report import build_daily_report
from .forward_report import build_forward_report
from .journal import Journal
from .project_state import save_project_state


MANIFEST_PATH = Path("agents/gloc/agent_manifest.json")
QUEUE_DIR = Path("agents/gloc/queue")
PENDING_PATH = QUEUE_DIR / "pending.jsonl"
DONE_PATH = QUEUE_DIR / "done.jsonl"
LOG_DIR = Path("agents/gloc/logs")


def agent_status() -> str:
    manifest = load_manifest()
    lines = ["GLOC LOCAL AGENT RUNTIME", "=" * 72]
    lines.append(f"mode: {manifest.get('mode')}")
    lines.append(f"pending_tasks: {len(read_jsonl(PENDING_PATH))}")
    lines.append(f"done_tasks: {len(read_jsonl(DONE_PATH))}")
    lines.append("")
    for key, data in manifest.get("agents", {}).items():
        blocked = ", ".join(data.get("blocked_actions", []))
        allowed = ", ".join(data.get("allowed_actions", []))
        lines.append(f"{key}: {data.get('name')}")
        lines.append(f"  allowed: {allowed}")
        lines.append(f"  blocked: {blocked}")
    lines.append("")
    lines.append("SAFE: Vloc Executor is OFF. No order actions are allowed.")
    return "\n".join(lines)


def enqueue_task(agent: str, action: str, note: str = "") -> str:
    manifest = load_manifest()
    validate_agent_action(manifest, agent, action)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    task = {
        "id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "note": note,
        "status": "pending",
    }
    with PENDING_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(task, ensure_ascii=False) + "\n")
    return f"queued: {task['id']} {agent}.{action}"


def run_agent_once(agent: str, configs: list[dict]) -> str:
    manifest = load_manifest()
    if agent not in manifest.get("agents", {}):
        return f"unknown agent: {agent}"
    tasks = read_jsonl(PENDING_PATH)
    selected = None
    remaining = []
    for task in tasks:
        if selected is None and task.get("agent") == agent:
            selected = task
        else:
            remaining.append(task)
    write_jsonl(PENDING_PATH, remaining)
    if selected is None:
        return f"no pending task for {agent}"

    action = selected["action"]
    validate_agent_action(manifest, agent, action)
    output = run_action(agent, action, configs)
    selected["status"] = "done"
    selected["finished_at"] = datetime.now(timezone.utc).isoformat()
    selected["output_preview"] = output[:500]
    append_jsonl(DONE_PATH, selected)
    write_agent_log(agent, selected, output)
    return output


def run_agent_loop(agent: str, configs: list[dict], interval_seconds: int = 30, max_cycles: int = 0) -> str:
    cycles = 0
    lines = [
        f"agent_loop_started: {agent}",
        f"interval_seconds: {interval_seconds}",
        "press Ctrl+C to stop",
    ]
    print("\n".join(lines))
    while True:
        cycles += 1
        output = run_agent_once(agent, configs)
        if not output.startswith("no pending task"):
            print("")
            print(f"[{datetime.now().isoformat(timespec='seconds')}] {agent}")
            print(output)
        if max_cycles and cycles >= max_cycles:
            return f"agent_loop_stopped: {agent} cycles={cycles}"
        time.sleep(max(interval_seconds, 1))


def run_action(agent: str, action: str, configs: list[dict]) -> str:
    if action == "status":
        return agent_status()
    if action == "safe-automation":
        return run_safe_automation(configs, send_discord=False)
    if action == "save-state":
        return f"saved: {save_project_state(configs, 'PROJECT_STATE.md')}"
    if action == "backup":
        return run_backup(
            [
                "config.json",
                "config_btc.json",
                "PROJECT_STATE.md",
                "PROJECT_MEMORY.md",
                "AI_RUNBOOK.md",
                "SOUL.md",
                "AGENT_RULES.md",
                "TRADE_LESSONS.md",
                "journal_btc_current.sqlite",
                "journal_xau_current.sqlite",
            ],
            "backups",
        )
    if action == "report":
        return "\n\n".join(build_symbol_report(config) for config in configs)
    if action == "daily":
        return "\n\n".join(build_symbol_daily(config) for config in configs)
    if action == "execution-status":
        from .execution import execution_status

        return "\n\n".join(execution_status(config) for config in configs)
    if action == "resend-latest":
        from .alerts import resend_latest_signal

        return resend_latest_signal(configs[0])
    return f"action not implemented for {agent}: {action}"


def build_symbol_report(config: dict) -> str:
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    start_at = config.get("report", {}).get("forward_start")
    return build_forward_report(journal.all_signals(), target_signals=50, start_at=start_at)


def build_symbol_daily(config: dict) -> str:
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    start_at = config.get("report", {}).get("forward_start")
    return build_daily_report(journal.all_signals(), days=7, start_at=start_at)


def validate_agent_action(manifest: dict, agent: str, action: str) -> None:
    agents = manifest.get("agents", {})
    if agent not in agents:
        raise ValueError(f"unknown agent: {agent}")
    if action in agents[agent].get("blocked_actions", []):
        raise ValueError(f"blocked action for {agent}: {action}")
    if action not in agents[agent].get("allowed_actions", []):
        raise ValueError(f"action not allowed for {agent}: {action}")


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_agent_log(agent: str, task: dict, output: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"{stamp}_{agent}_{task['action']}.log"
    path.write_text(output + "\n", encoding="utf-8")
