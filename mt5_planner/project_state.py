from datetime import datetime
from pathlib import Path

from .forward_report import build_forward_report
from .daily_report import build_daily_report
from .journal import Journal


def save_project_state(configs: list[dict], output: str = "PROJECT_STATE.md") -> str:
    lines = []
    lines.append("# MT5 Planner Project State")
    lines.append("")
    lines.append(f"saved_at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Current Mode")
    lines.append("")
    lines.append("- Forward test / paper signal only")
    lines.append("- Auto execution OFF")
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
        lines.append(build_forward_report(journal.all_signals(), target_signals=50, start_at=start_at))
        lines.append("```")
        lines.append("")
        lines.append("```text")
        lines.append(build_daily_report(journal.all_signals(), days=7, start_at=start_at))
        lines.append("```")
        lines.append("")

    lines.append("## Next Recommended Actions")
    lines.append("")
    lines.append("1. Keep `01 Gloc BTC Live` running while BTC feed is active.")
    lines.append("2. Use `02 Gloc XAU Live Weekdays` only when the gold market is open.")
    lines.append("3. Use `03 Gloc Dashboard Live` for live view and manual marks.")
    lines.append("4. Use `04 Gloc Safe Automation` for report, daily, save-state, backup, and Discord digest.")
    lines.append("5. Collect 50-100 forward signals before strategy or execution changes.")
    lines.append("6. Keep auto execution disabled until forward data passes the gate.")
    lines.append("")

    path = Path(output)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
