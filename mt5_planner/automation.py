from pathlib import Path

from .alerts import send_discord_alert
from .backup import run_backup
from .daily_report import build_daily_report
from .forward_report import build_forward_report
from .journal import Journal
from .order_ledger import build_order_report, sync_order_ledger
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
    "orders_btcusdm_current.sqlite",
    "orders_xauusdm_current.sqlite",
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
        forward = build_forward_report(rows, target_signals=50, start_at=start_at, config=config)
        daily = build_daily_report(rows, days=7, start_at=start_at)
        try:
            order_sync = sync_order_ledger(config, start_at=start_at)
            order_report = build_order_report(config, start_at=start_at)
        except Exception as exc:
            order_sync = f"order ledger sync skipped: {exc}"
            order_report = order_sync

        forward_path = report_dir / f"forward_{symbol_key}.txt"
        daily_path = report_dir / f"daily_{symbol_key}.txt"
        order_path = report_dir / f"orders_{symbol_key}.txt"
        forward_path.write_text(forward + "\n", encoding="utf-8")
        daily_path.write_text(daily + "\n", encoding="utf-8")
        order_path.write_text(order_report + "\n", encoding="utf-8")

        lines.append(f"{config['symbol']} {config['timeframe']}")
        lines.append(f"- forward_report: {forward_path}")
        lines.append(f"- daily_report: {daily_path}")
        lines.append(f"- order_report: {order_path}")
        lines.append(f"- order_sync: {order_sync}")
        lines.append(f"- execution_enabled: {config.get('execution', {}).get('enabled', False)}")
        lines.append("")

        discord_lines.extend(discord_summary(config, forward, daily, order_report))

    state_path = save_project_state(configs, "PROJECT_STATE.md")
    backup_result = run_backup(BACKUP_FILES, backup_dir)
    lines.append(f"project_state: {state_path}")
    lines.append(backup_result)
    lines.append("")
    lines.append("SAFE: report/save-state/backup only. No order sending was performed by this automation.")

    if send_discord and configs:
        discord_lines.append("")
        discord_lines.append("Automation action: report/save-state/backup only")
        discord_lines.append(f"State saved: {state_path}")
        send_discord_alert(
            configs[0].get("alerts", {}),
            discord_lines,
            route="reports",
            title="SAFE AUTOMATION DIGEST",
            status_text="Safe digest only | no order action",
        )
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


def discord_summary(config: dict, forward: str, daily: str, order_report: str) -> list[str]:
    forward_lines = forward.splitlines()
    daily_lines = daily.splitlines()
    order_lines = order_report.splitlines()
    picked = [
        line
        for line in forward_lines
        if line.startswith(("raw signals:", "grouped trade ideas:", "execution:", "MT5 today/history:", "expectancy:", "progress:", "decision:"))
    ]
    total = next((line for line in daily_lines if line.startswith("signals ")), "")
    order_total = next((line for line in order_lines if line.startswith("orders:")), "")
    order_pnl = next((line for line in order_lines if line.startswith("closed P/L:")), "")
    result = [f"**{config['symbol']} {config['timeframe']}**"]
    result.extend(picked[:5])
    if total:
        result.append(total)
    if order_total:
        result.append(order_total)
    if order_pnl:
        result.append(order_pnl)
    return result[:8]
