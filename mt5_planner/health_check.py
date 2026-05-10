from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3

import pandas as pd

from .alerts import ROUTE_ENV
from .execution import execution_guard_status
from .mt5_runtime import initialize_mt5
from .order_ledger import build_order_report, ledger_path, sync_order_ledger


def build_health_check(configs: list[dict]) -> str:
    lines = ["GLOC HEALTH CHECK", "=" * 72]
    lines.append(f"checked_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append("")
    lines.extend(discord_section())
    lines.append("")
    for config in configs:
        lines.extend(symbol_health(config))
        lines.append("")
    return "\n".join(lines).rstrip()


def discord_section() -> list[str]:
    lines = ["DISCORD ROUTES"]
    for route in ("signals", "reports", "ops", "chat"):
        env = ROUTE_ENV[route]
        lines.append(f"- {route:<7} {'OK' if os.environ.get(env) else 'missing'} ({env})")
    return lines


def symbol_health(config: dict) -> list[str]:
    symbol = config.get("symbol", "-")
    timeframe = config.get("timeframe", "-")
    execution = config.get("execution", {})
    guard = execution_guard_status(config)
    csv = csv_status(config)
    journal_count = count_rows(config.get("journal_path", "journal.sqlite"), "signals")
    order_count = count_rows(ledger_path(config), "mt5_orders")
    mt5 = mt5_status(config)

    lines = [f"{symbol} {timeframe}", "-" * 72]
    lines.append(
        f"execution: {state_text(execution)} | max_open {execution.get('max_open_trades', 1)} | "
        f"daily_loss_limit ${float(execution.get('daily_max_loss_usd') or 0):.2f}"
    )
    lines.append(f"guards: daily_locked={guard['daily_locked']} | duplicate_file={guard['duplicate_seen_file']}")
    lines.append(f"csv: {csv}")
    lines.append(f"journal rows: {journal_count} | order ledger rows: {order_count}")
    lines.append(f"MT5: {mt5}")
    try:
        sync_order_ledger(config, start_at=config.get("report", {}).get("forward_start"))
        order_lines = build_order_report(config, start_at=config.get("report", {}).get("forward_start")).splitlines()
        picked = [
            line for line in order_lines
            if line.startswith(("orders:", "closed P/L:", "gross win"))
        ]
        if picked:
            lines.append("orders: " + " | ".join(picked))
    except Exception as exc:
        lines.append(f"orders: sync skipped ({exc})")
    return lines


def state_text(execution: dict) -> str:
    if not execution.get("enabled", False):
        return "OFF"
    if execution.get("dry_run", True):
        return "DRY RUN"
    if execution.get("demo_only", True):
        return "DEMO AUTO ON"
    return "ENABLED"


def csv_status(config: dict) -> str:
    path = Path(config.get("csv_path", ""))
    if not path.exists():
        return f"missing {path}"
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    try:
        rows = len(pd.read_csv(path))
    except Exception:
        rows = -1
    row_text = f"{rows} rows" if rows >= 0 else "read failed"
    age_seconds = int(age.total_seconds())
    state = "OK" if age_seconds <= 900 else "STALE"
    return f"{state} {path} | {row_text} | age {age_seconds}s"


def mt5_status(config: dict) -> str:
    try:
        mt5 = initialize_mt5(config)
        account = mt5.account_info()
        symbol = config.get("symbol")
        positions = mt5.positions_get(symbol=symbol) or []
        magic = int(config.get("execution", {}).get("magic", 0) or 0)
        owned = [
            position for position in positions
            if not magic or int(getattr(position, "magic", 0) or 0) == magic
        ]
        trade_mode = getattr(account, "trade_mode", "-") if account else "-"
        mt5.shutdown()
        return f"connected | trade_mode {trade_mode} | Vloc positions {len(owned)}"
    except Exception as exc:
        try:
            mt5.shutdown()
        except Exception:
            pass
        return f"unavailable ({exc})"


def count_rows(path: str, table: str) -> int:
    db = Path(path)
    if not db.exists():
        return 0
    try:
        with sqlite3.connect(db) as conn:
            return int(conn.execute(f"select count(*) from {table}").fetchone()[0])
    except Exception:
        return 0
