from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from .alerts import send_discord_alert
from .mt5_runtime import initialize_mt5


def manage_demo_positions(config: dict) -> list[dict]:
    execution = config.get("execution", {})
    if not execution.get("enabled", False):
        return []
    if execution.get("mode") != "demo_auto":
        return []
    if not execution.get("manage_positions", True):
        return []

    try:
        mt5 = initialize_mt5(config)
        if execution.get("demo_only", True):
            account = mt5.account_info()
            demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
            if account is None or account.trade_mode != demo_mode:
                raise RuntimeError("blocked: MT5 account is not demo")

        symbol = config["symbol"]
        magic = int(execution.get("magic", 505501))
        positions = mt5.positions_get(symbol=symbol) or []
        results = []
        for position in positions:
            if int(getattr(position, "magic", 0) or 0) != magic:
                continue
            result = manage_position(mt5, config, position)
            if result:
                append_manager_log(result)
                notify_manager(config, result)
                results.append(result)
        return results
    except Exception as exc:
        result = base_manager_result(config, None)
        result.update({"status": "error", "reason": str(exc)})
        append_manager_log(result)
        notify_manager(config, result)
        return [result]


def manage_position(mt5, config: dict, position) -> dict | None:
    execution = config.get("execution", {})
    symbol = config["symbol"]
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    if tick is None or info is None:
        return manager_result(config, position, "error", "missing tick or symbol info")

    pos_type = int(position.type)
    is_buy = pos_type == mt5.POSITION_TYPE_BUY
    price = float(tick.bid if is_buy else tick.ask)
    entry = float(position.price_open)
    sl = float(position.sl or 0)
    tp = float(position.tp or 0)
    if sl <= 0:
        return None

    risk = abs(entry - sl)
    if risk <= 0:
        return None

    current_r = (price - entry) / risk if is_buy else (entry - price) / risk
    tp1_rr = float(execution.get("tp1_rr", execution.get("move_be_at_rr", 1.0)) or 1.0)
    move_be_rr = float(execution.get("move_be_at_rr", tp1_rr) or tp1_rr)
    results = []

    if current_r >= tp1_rr and not already_partially_closed(position, info):
        partial = partial_close(mt5, config, position, is_buy, tick, info)
        if partial:
            results.append(partial)

    if current_r >= move_be_rr and should_move_to_be(position, is_buy):
        be = move_stop_to_break_even(mt5, config, position, is_buy)
        if be:
            results.append(be)

    if not results:
        return None

    merged = manager_result(config, position, "managed", "; ".join(r["reason"] for r in results))
    merged["actions"] = results
    merged["current_r"] = round(current_r, 3)
    return merged


def partial_close(mt5, config: dict, position, is_buy: bool, tick, info) -> dict | None:
    execution = config.get("execution", {})
    ratio = float(execution.get("partial_close_ratio", 0.5) or 0)
    if ratio <= 0:
        return None

    min_lot = float(getattr(info, "volume_min", 0.01) or 0.01)
    step = float(getattr(info, "volume_step", 0.01) or 0.01)
    volume = round_volume(float(position.volume) * ratio, step)
    remaining = float(position.volume) - volume
    if volume < min_lot or remaining < min_lot:
        return manager_result(config, position, "skip", "partial close skipped: volume below min lot")

    close_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY
    price = float(tick.bid if is_buy else tick.ask)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": config["symbol"],
        "position": int(position.ticket),
        "volume": volume,
        "type": close_type,
        "price": price,
        "deviation": int(config.get("execution", {}).get("deviation_points", 50)),
        "magic": int(config.get("execution", {}).get("magic", 505501)),
        "comment": "Gloc TP1 partial",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    response = mt5.order_send(request)
    if response is None:
        return manager_result(config, position, "error", f"partial close failed: {mt5.last_error()}")
    status = "partial_closed" if response.retcode == mt5.TRADE_RETCODE_DONE else "reject"
    return manager_result(config, position, status, f"partial close retcode {response.retcode}")


def move_stop_to_break_even(mt5, config: dict, position, is_buy: bool) -> dict | None:
    entry = float(position.price_open)
    current_sl = float(position.sl or 0)
    be_offset = float(config.get("execution", {}).get("be_offset_points", 0) or 0)
    point = mt5.symbol_info(config["symbol"]).point
    new_sl = entry + be_offset * point if is_buy else entry - be_offset * point
    if is_buy and current_sl >= new_sl:
        return None
    if not is_buy and current_sl <= new_sl:
        return None
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": config["symbol"],
        "position": int(position.ticket),
        "sl": round(new_sl, 3),
        "tp": float(position.tp or 0),
    }
    response = mt5.order_send(request)
    if response is None:
        return manager_result(config, position, "error", f"move BE failed: {mt5.last_error()}")
    status = "be_moved" if response.retcode == mt5.TRADE_RETCODE_DONE else "reject"
    return manager_result(config, position, status, f"move SL to BE retcode {response.retcode}")


def should_move_to_be(position, is_buy: bool) -> bool:
    entry = float(position.price_open)
    sl = float(position.sl or 0)
    if is_buy:
        return sl < entry
    return sl > entry


def already_partially_closed(position, info) -> bool:
    min_lot = float(getattr(info, "volume_min", 0.01) or 0.01)
    return float(position.volume) <= min_lot


def round_volume(value: float, step: float) -> float:
    if step <= 0:
        return value
    return round(int(value / step) * step, 2)


def manager_result(config: dict, position, status: str, reason: str) -> dict:
    result = base_manager_result(config, position)
    result.update({"status": status, "reason": reason})
    return result


def base_manager_result(config: dict, position) -> dict:
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "symbol": config.get("symbol"),
        "ticket": int(getattr(position, "ticket", 0) or 0) if position else 0,
        "volume": float(getattr(position, "volume", 0) or 0) if position else 0,
        "entry": float(getattr(position, "price_open", 0) or 0) if position else 0,
        "sl": float(getattr(position, "sl", 0) or 0) if position else 0,
        "tp": float(getattr(position, "tp", 0) or 0) if position else 0,
    }


def append_manager_log(result: dict) -> None:
    log_dir = Path("reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "manager.log").open("a", encoding="utf-8") as file:
        file.write(json.dumps(result, ensure_ascii=False) + "\n")


def notify_manager(config: dict, result: dict) -> None:
    settings = config.get("alerts", {})
    line = (
        f"{result.get('symbol')} | ticket {result.get('ticket')} | "
        f"status {result.get('status')} | reason {result.get('reason')}"
    )
    send_discord_alert(settings, [line], route="ops", title="VLOC MANAGER")
