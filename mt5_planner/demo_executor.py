from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from .execution import execution_guard_status
from .alerts import discord_status_text, send_discord_alert
from .mt5_runtime import initialize_mt5


def execute_saved_plans(config: dict, plans: list[dict]) -> list[dict]:
    if not plans:
        return []

    execution = config.get("execution", {})
    if not execution.get("enabled", False):
        return []

    results = []
    for plan in plans:
        result = execute_plan(config, plan)
        results.append(result)
        append_execution_log(result)
        notify_execution(config, result)
    return results


def execute_latest_signal(config: dict, force_dry_run: bool = True) -> list[dict]:
    alert_dir = Path(config.get("alerts", {}).get("dir", "reports"))
    latest = alert_dir / "latest_signal.json"
    if not latest.exists():
        plans = latest_journal_plans(config)
    else:
        payload = json.loads(latest.read_text(encoding="utf-8"))
        plans = payload.get("plans") or []
    if not plans:
        return [{"status": "reject", "reason": f"latest signal not found: {latest} or journal"}]
    if force_dry_run:
        config = dict(config)
        execution = dict(config.get("execution", {}))
        execution["enabled"] = True
        execution["dry_run"] = True
        execution["mode"] = "demo_auto"
        config["execution"] = execution
    return [execute_plan(config, plan) for plan in plans]


def latest_journal_plans(config: dict, limit: int = 1) -> list[dict]:
    path = Path(config.get("journal_path", "journal.sqlite"))
    if not path.exists():
        return []
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            select payload
            from signals
            where coalesce(source, 'forward') = 'forward'
            order by id desc
            limit ?
            """,
            (limit,),
        ).fetchall()
    plans = []
    for row in rows:
        try:
            plans.append(json.loads(row["payload"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return plans


def execute_plan(config: dict, plan: dict) -> dict:
    execution = config.get("execution", {})
    result = base_result(config, plan)
    allowed, reason = preflight(config, plan)
    if not allowed:
        result.update({"status": "reject", "reason": reason})
        return result

    if execution.get("dry_run", True):
        result.update({"status": "dry_run", "reason": "validated; order not sent"})
        return result

    try:
        order_result = send_mt5_market_order(config, plan)
    except Exception as exc:
        result.update({"status": "error", "reason": str(exc)})
        return result

    mark_duplicate_seen(config, plan)
    result.update(order_result)
    return result


def preflight(config: dict, plan: dict) -> tuple[bool, str]:
    execution = config.get("execution", {})
    if execution.get("mode") != "demo_auto":
        return False, "execution.mode must be demo_auto"
    if not execution.get("demo_only", True):
        return False, "demo_only must stay true"
    if execution.get("emergency_stop", True) is False:
        return False, "emergency_stop disabled"

    guard = execution_guard_status(config)
    if guard["daily_locked"]:
        return False, f"daily locked: {guard['daily_lock_file']}"

    risk_warning = plan.get("risk_warning")
    if risk_warning:
        return False, f"risk guard: {risk_warning}"

    daily_loss = current_daily_loss_usd(config)
    max_daily_loss = float(execution.get("daily_max_loss_usd") or 0)
    if max_daily_loss > 0 and daily_loss >= max_daily_loss:
        return False, f"daily loss guard: ${daily_loss:.2f} >= ${max_daily_loss:.2f}"

    if duplicate_seen(config, plan):
        return False, "duplicate signal already seen"

    lot = float(plan.get("lot") or 0)
    max_lot = float(config.get("position_sizing", {}).get("max_lot", 1.0))
    if lot <= 0:
        return False, "lot must be > 0"
    if lot > max_lot:
        return False, f"lot {lot} > max_lot {max_lot}"

    if float(plan.get("actual_risk_usd") or 0) <= 0:
        return False, "actual risk must be > 0"

    return True, "ok"


def send_mt5_market_order(config: dict, plan: dict) -> dict:
    mt5 = initialize_mt5(config)

    symbol = config["symbol"]
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"symbol_select failed for {symbol}: {mt5.last_error()}")

    account = mt5.account_info()
    if account is None:
        raise RuntimeError(f"account_info failed: {mt5.last_error()}")
    demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
    if config.get("execution", {}).get("demo_only", True) and account.trade_mode != demo_mode:
        raise RuntimeError(f"blocked: account trade_mode {account.trade_mode} is not demo")

    open_count = open_position_count(mt5, symbol)
    max_open = int(config.get("execution", {}).get("max_open_trades", 1))
    if open_count >= max_open:
        raise RuntimeError(f"max_open_trades reached: {open_count}/{max_open}")

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"symbol_info_tick failed for {symbol}: {mt5.last_error()}")
    spread = abs(float(tick.ask) - float(tick.bid))
    max_spread = float(config.get("spread_filter", {}).get("max_spread_price") or 0)
    if max_spread > 0 and spread > max_spread:
        raise RuntimeError(f"spread guard: {spread:.3f} > {max_spread:.3f}")

    direction = str(plan.get("direction")).lower()
    order_type = mt5.ORDER_TYPE_BUY if direction == "long" else mt5.ORDER_TYPE_SELL
    price = float(tick.ask if direction == "long" else tick.bid)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(plan["lot"]),
        "type": order_type,
        "price": price,
        "sl": float(plan["stop_loss"]),
        "tp": float(plan["take_profit"]),
        "deviation": int(config.get("execution", {}).get("deviation_points", 50)),
        "magic": int(config.get("execution", {}).get("magic", 505501)),
        "comment": "Gloc demo auto",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    response = mt5.order_send(request)
    if response is None:
        raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
    status = "sent" if response.retcode == mt5.TRADE_RETCODE_DONE else "reject"
    return {
        "status": status,
        "reason": getattr(response, "comment", ""),
        "retcode": int(response.retcode),
        "order": int(getattr(response, "order", 0) or 0),
        "deal": int(getattr(response, "deal", 0) or 0),
        "price": price,
    }


def open_position_count(mt5, symbol: str) -> int:
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return 0
    return len(positions)


def current_daily_loss_usd(config: dict) -> float:
    path = Path(config.get("journal_path", "journal.sqlite"))
    if not path.exists():
        return 0.0
    today = datetime.now(timezone.utc).date().isoformat()
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(
            """
            select
                created_at, symbol, timeframe, mode, direction,
                entry, stop_loss, take_profit, risk_reward,
                quality_score, quality_label, session, spread, lot,
                actual_risk_usd, idea_key, status, closed_at, close_price,
                mfe, mae, source, payload
            from signals
            where coalesce(source, 'forward') = 'forward'
              and coalesce(closed_at, created_at) >= ?
            order by id asc
            """,
            (today,),
        ).fetchall()]
    from .forward_report import group_trade_ideas

    ideas = group_trade_ideas(rows)
    return sum(float(row.get("actual_risk_usd") or 0) for row in ideas if row.get("status") == "sl")


def signal_key(config: dict, plan: dict) -> str:
    return "|".join(
        [
            str(config.get("symbol", "")),
            str(config.get("timeframe", "")),
            str(plan.get("candle_time", "")),
            str(plan.get("idea_key") or ""),
            str(plan.get("direction") or ""),
        ]
    )


def duplicate_seen(config: dict, plan: dict) -> bool:
    if not config.get("execution", {}).get("duplicate_guard", True):
        return False
    seen = read_seen(config)
    return signal_key(config, plan) in seen


def mark_duplicate_seen(config: dict, plan: dict) -> None:
    if not config.get("execution", {}).get("duplicate_guard", True):
        return
    path = seen_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = read_seen(config)
    seen[signal_key(config, plan)] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8")


def read_seen(config: dict) -> dict:
    path = seen_path(config)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def seen_path(config: dict) -> Path:
    return Path(execution_guard_status(config)["duplicate_seen_file"])


def append_execution_log(result: dict) -> None:
    log_dir = Path("reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "execution.log").open("a", encoding="utf-8") as file:
        file.write(json.dumps(result, ensure_ascii=False) + "\n")


def notify_execution(config: dict, result: dict) -> None:
    reason = str(result.get("reason") or "")
    if result.get("status") in ("reject", "error") and reason.startswith("max_open_trades reached"):
        return
    settings = config.get("alerts", {})
    line = (
        f"{result.get('symbol')} {result.get('timeframe')} | {str(result.get('direction')).upper()} | "
        f"status {result.get('status')} | lot {float(result.get('lot') or 0):.2f} | "
        f"risk ${float(result.get('risk_usd') or 0):.2f} | reason {reason or '-'}"
    )
    send_discord_alert(
        settings,
        [line],
        route="ops",
        title="VLOC EXECUTION",
        status_text=discord_status_text(config),
    )


def base_result(config: dict, plan: dict) -> dict:
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "symbol": config.get("symbol"),
        "timeframe": config.get("timeframe"),
        "mode": plan.get("mode"),
        "direction": plan.get("direction"),
        "entry": plan.get("entry"),
        "sl": plan.get("stop_loss"),
        "tp": plan.get("take_profit"),
        "lot": plan.get("lot"),
        "risk_usd": plan.get("actual_risk_usd"),
        "idea_key": plan.get("idea_key"),
    }
