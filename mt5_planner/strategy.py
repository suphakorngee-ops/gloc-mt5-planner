from .market_features import structure_direction
from .position_sizing import apply_position_sizing
from .setups import detect_setup
from .quality import session_label
from .session_rules import session_profile


def build_trade_plans(df, config: dict) -> list[dict]:
    return analyze_trade(df, config)["plans"]


def analyze_trade(df, config: dict) -> dict:
    last = df.dropna().iloc[-1]
    prev = df.dropna().iloc[-2]
    settings = config.get("strategy", {})
    min_rr = float(settings.get("min_rr", 1.5))

    direction = detect_direction(df.dropna(), settings)
    if direction == "neutral":
        return {"plans": [], "direction": "neutral", "block_reason": "trend filter not confirmed"}

    setup = detect_setup(df, direction, settings)
    if not setup["ok"]:
        return {
            "plans": [],
            "direction": direction,
            "setup": setup,
            "block_reason": setup["reason"],
        }
    setup_block_reason = setup_quality_block(setup["name"], settings)
    if setup_block_reason:
        return {
            "plans": [],
            "direction": direction,
            "setup": setup,
            "block_reason": setup_block_reason,
        }

    entry = float(last["close"])
    atr = float(last["atr"])
    swing_high = float(last["swing_high"])
    swing_low = float(last["swing_low"])
    candle_time = str(last["time"])
    session = session_label(last["time"])
    if session in set(settings.get("blocked_sessions", [])):
        return {
            "plans": [],
            "direction": direction,
            "setup": setup,
            "block_reason": f"session blocked by strategy: {session}",
        }
    profile = session_profile(session, config)

    specs = {
        "safe": {"sl_atr": 1.4, "target_rr": 1.5, "risk_mult": 0.5, "entry_style": "pullback"},
        "mid": {"sl_atr": 1.1, "target_rr": 2.0, "risk_mult": 1.0, "entry_style": "current"},
        "aggressive": {"sl_atr": 0.8, "target_rr": 3.0, "risk_mult": 0.5, "entry_style": "breakout_only"},
    }
    enabled_modes = set(settings.get("enabled_modes", ["safe", "mid"]))

    plans = []
    for mode, spec in specs.items():
        if mode not in enabled_modes:
            continue
        spec = dict(spec)
        spec["sl_atr"] *= float(profile.get("sl_atr_mult", 1.0))
        spec["target_rr"] *= float(profile.get("target_rr_mult", 1.0))
        if spec["entry_style"] == "breakout_only" and "breakout" not in setup["name"]:
            continue
        plan_entry = planned_entry(entry, atr, direction, spec["entry_style"])
        if direction == "long":
            stop_loss = min(plan_entry - atr * spec["sl_atr"], swing_low)
            risk = plan_entry - stop_loss
            rr_tp = plan_entry + risk * spec["target_rr"]
            take_profit = max(swing_high, rr_tp)
            reward = take_profit - plan_entry
        else:
            stop_loss = max(plan_entry + atr * spec["sl_atr"], swing_high)
            risk = stop_loss - plan_entry
            rr_tp = plan_entry - risk * spec["target_rr"]
            take_profit = min(swing_low, rr_tp)
            reward = plan_entry - take_profit

        if risk <= 0:
            continue

        rr = reward / risk
        if rr < min_rr and mode != "safe":
            continue

        plan = {
                "mode": mode,
                "direction": direction,
                "entry": round(plan_entry, 3),
                "stop_loss": round(stop_loss, 3),
                "take_profit": round(take_profit, 3),
                "risk_reward": round(rr, 2),
                "risk_pct": round(float(config.get("risk_per_trade", 0.005)) * spec["risk_mult"], 5),
                "candle_time": candle_time,
                "setup": setup["name"],
                "setup_reason": setup["reason"],
                "session_profile": session,
                "valid_for_bars": int(settings.get("valid_for_bars", 2)),
                "tp1_rr": profile.get("tp1_rr", 1.0),
                "move_be_at_rr": profile.get("move_be_at_rr", 1.0),
                "reason": reason_text(direction, last, setup),
            }
        plans.append(apply_position_sizing(plan, config))

    return {"plans": plans, "direction": direction, "setup": setup, "block_reason": None}


def planned_entry(entry: float, atr: float, direction: str, style: str) -> float:
    if style != "pullback":
        return entry
    offset = atr * 0.25
    if direction == "long":
        return entry - offset
    if direction == "short":
        return entry + offset
    return entry


def setup_quality_block(setup_name: str, settings: dict) -> str | None:
    if not bool(settings.get("filter_low_edge_setups", True)):
        return None

    allowlist = settings.get("setup_allowlist", [])
    if allowlist and not any(token in setup_name for token in allowlist):
        return f"setup not in allowlist: {setup_name}"

    denylist = settings.get("setup_denylist", [])
    if any(token in setup_name for token in denylist):
        return f"setup blocked by denylist: {setup_name}"

    high_edge_tokens = settings.get(
        "high_edge_setup_tokens",
        ["vcp", "retest", "breakout", "sweep_", "wyckoff", "choch"],
    )
    if any(token in setup_name for token in high_edge_tokens):
        return None

    return f"low edge setup filtered: {setup_name}"


def detect_direction(data, settings: dict | None = None) -> str:
    settings = settings or {}
    method = settings.get("direction_method", "structure")
    if method == "structure":
        return structure_direction(data)

    last = data.iloc[-1]
    prev = data.iloc[-2]
    bullish = last["close"] > last["ema_fast"] > last["ema_slow"] and last["ema_fast"] >= prev["ema_fast"]
    bearish = last["close"] < last["ema_fast"] < last["ema_slow"] and last["ema_fast"] <= prev["ema_fast"]
    if bullish:
        return "long"
    if bearish:
        return "short"
    return "neutral"


def reason_text(direction: str, last, setup: dict) -> str:
    trend = "above" if direction == "long" else "below"
    return (
        f"price action bias {direction}, RSI {last['rsi']:.1f}, "
        f"ATR {last['atr']:.3f}; {setup['reason']}; plan uses structure + volatility stop"
    )
