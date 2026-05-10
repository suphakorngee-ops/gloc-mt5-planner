from datetime import datetime
from pathlib import Path

from .forward_report import build_forward_report
from .daily_report import build_daily_report
from .journal import Journal
from .order_ledger import build_order_report


def save_project_state(configs: list[dict], output: str = "PROJECT_STATE.md") -> str:
    lines = []
    lines.append("# MT5 Planner Project State")
    lines.append("")
    lines.append(f"saved_at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Current Mode")
    lines.append("")
    lines.append("- Forward tracking remains enabled")
    lines.append("- BTC demo auto execution may be ON if `config_btc.json` says enabled")
    lines.append("- XAU execution remains OFF unless explicitly changed")
    lines.append("- Fixed lot 0.01")
    lines.append("- Clean current journals")
    lines.append("")

    for config in configs:
        journal = Journal(config.get("journal_path", "journal.sqlite"))
        start_at = config.get("report", {}).get("forward_start")
        lines.append(f"## {config['symbol']} {config['timeframe']}")
        lines.append("")
        lines.append(f"- config: {config.get('_path', '-')}")
        lines.append(f"- journal: {config.get('journal_path')}")
        lines.append(f"- csv: {config.get('csv_path')}")
        lines.append(f"- fixed_lot: {config.get('position_sizing', {}).get('fixed_lot')}")
        lines.append(f"- execution_enabled: {config.get('execution', {}).get('enabled', False)}")
        lines.append("")
        lines.append("```text")
        lines.append(build_forward_report(journal.all_signals(), target_signals=50, start_at=start_at, config=config))
        lines.append("```")
        lines.append("")
        lines.append("```text")
        lines.append(build_daily_report(journal.all_signals(), days=7, start_at=start_at))
        lines.append("```")
        lines.append("")
        lines.append("```text")
        lines.append(build_order_report(config, start_at=start_at))
        lines.append("```")
        lines.append("")

    lines.append("## Next Recommended Actions")
    lines.append("")
    lines.append("1. Keep `LIVE 01 / BTC Demo Auto` running while BTC feed is active.")
    lines.append("2. Use `LIVE 02 / XAU Weekdays` only when the gold market is open.")
    lines.append("3. Use `EXEC 04 / Order Ledger All` to check actual MT5 P/L.")
    lines.append("4. Use `OPS 01 / Safe Automation` for report, daily, order ledger, save-state, backup, and Discord digest.")
    lines.append("5. Keep BTC auto execution demo-only with fixed lot 0.01 and guards.")
    lines.append("6. Keep XAU execution disabled until enough weekday forward data exists.")
    lines.append("")

    path = Path(output)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
