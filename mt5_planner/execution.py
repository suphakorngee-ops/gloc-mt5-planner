from datetime import datetime
from pathlib import Path


def execution_status(config: dict) -> str:
    settings = config.get("execution", {})
    enabled = bool(settings.get("enabled", False))
    guard = execution_guard_status(config)
    lines = []
    lines.append("AUTO EXECUTION STATUS")
    lines.append("=" * 72)
    lines.append(f"enabled: {enabled}")
    lines.append(f"mode: {settings.get('mode', 'manual_only')}")
    lines.append(f"dry_run: {settings.get('dry_run', True)}")
    lines.append(f"demo_only: {settings.get('demo_only', True)}")
    lines.append(f"max_open_trades: {settings.get('max_open_trades', 1)}")
    lines.append(f"daily_max_loss_usd: {settings.get('daily_max_loss_usd', 0)}")
    lines.append(f"duplicate_guard: {settings.get('duplicate_guard', True)}")
    lines.append(f"emergency_stop: {settings.get('emergency_stop', True)}")
    lines.append(f"manage_positions: {settings.get('manage_positions', False)}")
    lines.append(f"move_be_at_rr: {settings.get('move_be_at_rr', '-')}")
    lines.append(f"partial_close_ratio: {settings.get('partial_close_ratio', '-')}")
    lines.append(f"daily_lock_file: {guard['daily_lock_file']}")
    lines.append(f"daily_locked: {guard['daily_locked']}")
    lines.append(f"duplicate_seen_file: {guard['duplicate_seen_file']}")
    lines.append("")
    if enabled and settings.get("dry_run", True):
        lines.append("DRY RUN: execution gateway validates signals but does not send MT5 orders.")
    elif enabled:
        lines.append("DEMO AUTO: execution gateway can send MT5 demo orders if all guards pass.")
    else:
        lines.append("SAFE: execution gateway is OFF. Planner is manual/paper only.")
    lines.append("")
    lines.append("Before enabling in future:")
    lines.append("- 50-100 current forward signals unless user accepts demo-only early testing")
    lines.append("- positive expectancy and profit factor > 1.3")
    lines.append("- tested on demo/cent only")
    lines.append("- daily loss, duplicate order, and max trade guards verified")
    return "\n".join(lines)


def execution_guard_status(config: dict) -> dict:
    symbol = str(config.get("symbol", "symbol")).lower()
    today = datetime.now().strftime("%Y-%m-%d")
    guard_dir = Path("guards")
    daily_lock = guard_dir / f"{symbol}_{today}.lock"
    duplicate_seen = guard_dir / f"{symbol}_seen_signals.json"
    return {
        "daily_lock_file": str(daily_lock),
        "daily_locked": daily_lock.exists(),
        "duplicate_seen_file": str(duplicate_seen),
    }


def set_daily_lock(config: dict, reason: str = "manual lock") -> str:
    guard = execution_guard_status(config)
    path = Path(guard["daily_lock_file"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{datetime.now().isoformat()} | {reason}\n", encoding="utf-8")
    return str(path)


def clear_daily_lock(config: dict) -> str:
    guard = execution_guard_status(config)
    path = Path(guard["daily_lock_file"])
    if path.exists():
        path.unlink()
        return f"cleared: {path}"
    return f"not locked: {path}"
