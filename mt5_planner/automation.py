from pathlib import Path

from .alerts import send_discord_alert
from .backup import run_backup
from .daily_report import build_daily_report
from .forward_report import build_forward_report
from .journal import Journal
from .project_state import save_project_state


BACKUP_FILES = [
    "config.json",
    "config_btc.json",
    "config_xau_cent.json",
    "config_btc_cent.json",
    "PROJECT_STATE.md",
    "PROJECT_MEMORY.md",
    "USER_PLAYBOOK.md",
    "AI_RUNBOOK.md",
    "DISCORD_BOT_ROADMAP.md",
    "journal_xau_current.sqlite",
    "journal_btc_current.sqlite",
    "journal_xau_cent.sqlite",
    "journal_btc_cent.sqlite",
]


def run_safe_automation(
    configs: list[dict],
    *,
    send_discord: bool = False,
    output_dir: str = "reports",
    backup_dir: str = "backups",
) -> str:
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    lines = ["SAFE AUTOMATION RUN", "=" * 72]
    discord_lines = ["**Gloc Safe Automation**"]

    for config in configs:
        symbol_key = symbol_slug(config)
        journal = Journal(config.get("journal_path", "journal.sqlite"))
        rows = journal.all_signals()
        start_at = config.get("report", {}).get("forward_start")
        forward = build_forward_report(rows, target_signals=50, start_at=start_at)
        daily = build_daily_report(rows, days=7, start_at=start_at)

        forward_path = report_dir / f"forward_{symbol_key}.txt"
        daily_path = report_dir / f"daily_{symbol_key}.txt"
        forward_path.write_text(forward + "\n", encoding="utf-8")
        daily_path.write_text(daily + "\n", encoding="utf-8")

        lines.append(f"{config['symbol']} {config['timeframe']}")
        lines.append(f"- forward_report: {forward_path}")
        lines.append(f"- daily_report: {daily_path}")
        lines.append(f"- execution_enabled: {config.get('execution', {}).get('enabled', False)}")
        lines.append("")

        discord_lines.extend(discord_summary(config, forward, daily))

    state_path = save_project_state(configs, "PROJECT_STATE.md")
    backup_result = run_backup(BACKUP_FILES, backup_dir)
    lines.append(f"project_state: {state_path}")
    lines.append(backup_result)
    lines.append("")
    lines.append("SAFE: auto execution remains OFF. No order sending was performed.")

    if send_discord and configs:
        discord_lines.append("")
        discord_lines.append("Auto execution: OFF / manual-paper only")
        discord_lines.append(f"State saved: {state_path}")
        send_discord_alert(configs[0].get("alerts", {}), discord_lines, route="reports", title="SAFE AUTOMATION DIGEST")
        lines.append("discord_digest: requested")
    else:
        lines.append("discord_digest: skipped")

    return "\n".join(lines)


def symbol_slug(config: dict) -> str:
    symbol = str(config.get("symbol", "symbol")).lower()
    if "btc" in symbol:
        return "btc"
    if "xau" in symbol:
        return "xau"
    return symbol.replace("/", "_").replace(" ", "_")


def discord_summary(config: dict, forward: str, daily: str) -> list[str]:
    forward_lines = forward.splitlines()
    daily_lines = daily.splitlines()
    picked = [
        line
        for line in forward_lines
        if line.startswith(("signals:", "wins:", "expectancy:", "progress:", "decision:"))
    ]
    total = next((line for line in daily_lines if line.startswith("signals ")), "")
    result = [f"**{config['symbol']} {config['timeframe']}**"]
    result.extend(picked[:5])
    if total:
        result.append(total)
    return result[:8]
