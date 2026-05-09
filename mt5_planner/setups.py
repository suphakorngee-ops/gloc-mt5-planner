from .market_features import compute_market_features


def detect_setup(df, direction: str, settings: dict) -> dict:
    data = df.dropna().copy()
    if len(data) < 80:
        return {"name": "none", "ok": False, "reason": "not enough candles"}

    last = data.iloc[-1]
    prev = data.iloc[-2]

    flat = flat_base(data, settings)
    vcp = volatility_contraction(data, settings)
    breakout = breakout_signal(data, direction, settings)
    retest = retest_signal(data, direction, settings)
    features = compute_market_features(data, direction)

    passed = []
    if flat["ok"]:
        passed.append(flat["name"])
    if vcp["ok"]:
        passed.append(vcp["name"])
    if breakout["ok"]:
        passed.append(breakout["name"])
    if retest["ok"]:
        passed.append(retest["name"])
    if features.get("ok"):
        max_chase = float(settings.get("max_chase_position", 0.82))
        min_short_chase = float(settings.get("min_short_chase_position", 0.18))
        loc = features["location"]["position"]
        if direction == "long" and loc >= max_chase:
            return {
                "name": "none",
                "ok": False,
                "reason": f"avoid chasing near swing high: loc {loc}",
                "features": features,
            }
        if direction == "short" and loc <= min_short_chase:
            return {
                "name": "none",
                "ok": False,
                "reason": f"avoid chasing near swing low: loc {loc}",
                "features": features,
            }
        if features["smc"]["ok"]:
            passed.append(features["smc"]["event"])
        if features["smc_flow"]["ok"]:
            passed.append(features["smc_flow"]["event"])
        if features["fibo"]["ok"]:
            passed.append(f"fibo_{features['fibo']['zone']}")
        if features["scalp_momentum"]["ok"]:
            passed.append("scalp_momentum")

    require_confirmation = bool(settings.get("require_setup_confirmation", True))
    if require_confirmation and not (breakout["ok"] or retest["ok"]):
        allow_smc = bool(settings.get("allow_smc_confirmation", True))
        smc_ok = allow_smc and features.get("ok") and features["smc"]["ok"] and features["fibo"]["ok"]
        smc_flow_ok = allow_smc and features.get("ok") and features["smc_flow"]["ok"]
        pullback_ok = (
            bool(settings.get("allow_pullback_confirmation", True))
            and features.get("ok")
            and features["fibo"]["zone"] == "golden"
            and features["trend_follow"]["ok"]
            and not features["location"]["chase"]
        )
        if smc_ok or smc_flow_ok or pullback_ok:
            if pullback_ok:
                passed.append("pullback_fibo")
            return {
                "name": "+".join(passed),
                "ok": True,
                "reason": setup_reason(last, prev, passed),
                "features": features,
            }
        return {
            "name": "none",
            "ok": False,
            "reason": "waiting breakout/retest confirmation",
            "details": ", ".join(passed) or "no base",
        }

    if not passed:
        return {"name": "trend_only", "ok": not require_confirmation, "reason": "trend only"}

    return {
        "name": "+".join(passed),
        "ok": True,
        "reason": setup_reason(last, prev, passed),
        "details": ", ".join(passed),
        "features": features,
    }


def flat_base(data, settings: dict) -> dict:
    window = int(settings.get("base_window", 18))
    max_range_atr = float(settings.get("base_max_range_atr", 3.0))
    recent = data.tail(window)
    box_range = float(recent["high"].max() - recent["low"].min())
    atr = float(data.iloc[-1]["atr"])
    ok = atr > 0 and box_range / atr <= max_range_atr
    return {
        "name": "flat_base",
        "ok": ok,
        "range_atr": round(box_range / atr, 2) if atr > 0 else None,
    }


def volatility_contraction(data, settings: dict) -> dict:
    fast = int(settings.get("vcp_fast_window", 8))
    slow = int(settings.get("vcp_slow_window", 24))
    threshold = float(settings.get("vcp_threshold", 0.75))

    recent_range = (data["high"] - data["low"]).tail(fast).mean()
    prior_range = (data["high"] - data["low"]).tail(slow).head(slow - fast).mean()
    if prior_range <= 0:
        return {"name": "vcp", "ok": False, "ratio": None}

    ratio = float(recent_range / prior_range)
    return {"name": "vcp", "ok": ratio <= threshold, "ratio": round(ratio, 2)}


def breakout_signal(data, direction: str, settings: dict) -> dict:
    window = int(settings.get("breakout_window", 20))
    buffer_atr = float(settings.get("breakout_buffer_atr", 0.05))
    prev_data = data.iloc[:-1].tail(window)
    last = data.iloc[-1]
    buffer = float(last["atr"]) * buffer_atr

    if direction == "long":
        level = float(prev_data["high"].max())
        ok = float(last["close"]) > level + buffer
    else:
        level = float(prev_data["low"].min())
        ok = float(last["close"]) < level - buffer

    return {"name": "breakout", "ok": ok, "level": round(level, 3)}


def retest_signal(data, direction: str, settings: dict) -> dict:
    window = int(settings.get("breakout_window", 20))
    tolerance_atr = float(settings.get("retest_tolerance_atr", 0.25))
    prev_data = data.iloc[:-2].tail(window)
    last = data.iloc[-1]
    prev = data.iloc[-2]
    tolerance = float(last["atr"]) * tolerance_atr

    if direction == "long":
        level = float(prev_data["high"].max())
        touched = float(last["low"]) <= level + tolerance
        reclaimed = float(last["close"]) > level and float(last["close"]) > float(prev["close"])
        ok = touched and reclaimed
    else:
        level = float(prev_data["low"].min())
        touched = float(last["high"]) >= level - tolerance
        reclaimed = float(last["close"]) < level and float(last["close"]) < float(prev["close"])
        ok = touched and reclaimed

    return {"name": "retest", "ok": ok, "level": round(level, 3)}


def setup_reason(last, prev, passed: list[str]) -> str:
    return f"setup confirmed: {', '.join(passed)}"
