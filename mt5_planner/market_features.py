def compute_market_features(df, direction: str | None = None) -> dict:
    data = df.dropna().copy()
    if len(data) < 80:
        return {"ok": False, "reason": "not enough candles"}

    last = data.iloc[-1]
    prev = data.iloc[-2]
    recent = data.tail(20)
    prior = data.iloc[-40:-20]

    atr = float(last["atr"])
    close = float(last["close"])
    body = abs(float(last["close"]) - float(last["open"]))
    candle_range = max(float(last["high"]) - float(last["low"]), 0.000001)

    swing_high = float(recent["high"].max())
    swing_low = float(recent["low"].min())
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())

    trend_strength = structure_strength(data, direction)
    body_ratio = body / candle_range
    compression_ratio = range_mean(data.tail(8)) / range_mean(data.iloc[-24:-8])

    if direction is None:
        direction = infer_direction(last, prev)

    return {
        "ok": True,
        "direction": direction,
        "trend_strength": round(trend_strength, 3),
        "body_ratio": round(body_ratio, 3),
        "compression_ratio": round(compression_ratio, 3),
        "scalp_momentum": scalp_momentum(data, direction),
        "trend_follow": trend_follow(data, direction),
        "smc": smc_structure(data, direction, prior_high, prior_low),
        "smc_flow": smc_flow(data, direction),
        "fibo": fibo_zone(data, direction, swing_high, swing_low, close),
        "levels": structure_levels(data, direction, swing_high, swing_low, close),
        "location": price_location(direction, swing_high, swing_low, close),
    }


def infer_direction(last, prev) -> str:
    close = float(last["close"])
    prior_high = float(last.get("swing_high", close))
    prior_low = float(last.get("swing_low", close))
    prev_close = float(prev["close"])
    if close > prior_high or close > prev_close:
        return "long"
    if close < prior_low or close < prev_close:
        return "short"
    return "neutral"


def structure_direction(data) -> str:
    recent = data.tail(16)
    prior = data.iloc[-40:-16]
    if prior.empty:
        return "neutral"

    last = data.iloc[-1]
    close = float(last["close"])
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    recent_high = float(recent["high"].max())
    recent_low = float(recent["low"].min())
    midpoint = (prior_high + prior_low) / 2

    swept_low = recent_low < prior_low and close > prior_low
    swept_high = recent_high > prior_high and close < prior_high
    bos_up = close > prior_high
    bos_down = close < prior_low
    higher_structure = recent_high > prior_high and recent_low > prior_low and close > midpoint
    lower_structure = recent_low < prior_low and recent_high < prior_high and close < midpoint

    if bos_up or swept_low or higher_structure:
        return "long"
    if bos_down or swept_high or lower_structure:
        return "short"
    return "neutral"


def structure_strength(data, direction: str) -> float:
    prior = data.iloc[-40:-16]
    if prior.empty:
        return 0
    last = data.iloc[-1]
    atr = float(last["atr"])
    if atr <= 0:
        return 0
    close = float(last["close"])
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    if direction == "long":
        return max((close - prior_low) / atr, 0)
    if direction == "short":
        return max((prior_high - close) / atr, 0)
    return 0


def range_mean(data) -> float:
    if data.empty:
        return 1.0
    value = float((data["high"] - data["low"]).mean())
    return max(value, 0.000001)


def scalp_momentum(data, direction: str) -> dict:
    last3 = data.tail(3)
    bullish_closes = int((last3["close"] > last3["open"]).sum())
    bearish_closes = int((last3["close"] < last3["open"]).sum())
    close_change = float(data.iloc[-1]["close"] - data.iloc[-4]["close"])
    atr = float(data.iloc[-1]["atr"])

    if direction == "long":
        ok = bullish_closes >= 2 and close_change > 0 and close_change / atr >= 0.25
    elif direction == "short":
        ok = bearish_closes >= 2 and close_change < 0 and abs(close_change) / atr >= 0.25
    else:
        ok = False

    return {
        "ok": ok,
        "score": 1 if ok else 0,
        "change_atr": round(close_change / atr, 2) if atr > 0 else 0,
    }


def trend_follow(data, direction: str) -> dict:
    inferred = structure_direction(data)
    strength = structure_strength(data, direction)
    ok = direction != "neutral" and inferred == direction

    return {"ok": bool(ok), "strength": round(strength, 2)}


def smc_structure(data, direction: str, prior_high: float, prior_low: float) -> dict:
    last = data.iloc[-1]
    swept_high = float(last["high"]) > prior_high and float(last["close"]) < prior_high
    swept_low = float(last["low"]) < prior_low and float(last["close"]) > prior_low
    bos_up = float(last["close"]) > prior_high
    bos_down = float(last["close"]) < prior_low

    if direction == "long":
        ok = swept_low or bos_up
        event = "liquidity_sweep_low" if swept_low else "bos_up" if bos_up else "none"
    elif direction == "short":
        ok = swept_high or bos_down
        event = "liquidity_sweep_high" if swept_high else "bos_down" if bos_down else "none"
    else:
        ok = False
        event = "none"

    return {"ok": ok, "event": event}


def smc_flow(data, direction: str) -> dict:
    sweep = liquidity_sweep(data, direction)
    choch = choch_signal(data, direction)
    fvg = latest_fvg(data, direction)
    ob = order_block_proxy(data, direction)
    wyckoff = wyckoff_trap(data, direction)

    has_entry_zone = fvg["ok"] or ob["ok"]
    ok = (sweep["ok"] or wyckoff["ok"]) and choch["ok"] and has_entry_zone
    parts = []
    if sweep["ok"]:
        parts.append(sweep["event"])
    if wyckoff["ok"]:
        parts.append(wyckoff["event"])
    if choch["ok"]:
        parts.append(choch["event"])
    if fvg["ok"]:
        parts.append(fvg["event"])
    if ob["ok"]:
        parts.append(ob["event"])

    return {
        "ok": ok,
        "event": "+".join(parts) if parts else "none",
        "sweep": sweep,
        "choch": choch,
        "fvg": fvg,
        "order_block": ob,
        "wyckoff": wyckoff,
    }


def liquidity_sweep(data, direction: str) -> dict:
    recent = data.tail(8)
    prior = data.iloc[-28:-8]
    if prior.empty:
        return {"ok": False, "event": "none"}

    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    last = data.iloc[-1]
    swept_low = float(recent["low"].min()) < prior_low and float(last["close"]) > prior_low
    swept_high = float(recent["high"].max()) > prior_high and float(last["close"]) < prior_high

    if direction == "long" and swept_low:
        return {"ok": True, "event": "sweep_low"}
    if direction == "short" and swept_high:
        return {"ok": True, "event": "sweep_high"}
    return {"ok": False, "event": "none"}


def choch_signal(data, direction: str) -> dict:
    prior = data.iloc[-18:-3]
    last = data.iloc[-1]
    if prior.empty:
        return {"ok": False, "event": "none"}

    micro_high = float(prior["high"].max())
    micro_low = float(prior["low"].min())
    if direction == "long" and float(last["close"]) > micro_high:
        return {"ok": True, "event": "choch_up"}
    if direction == "short" and float(last["close"]) < micro_low:
        return {"ok": True, "event": "choch_down"}
    return {"ok": False, "event": "none"}


def latest_fvg(data, direction: str) -> dict:
    atr = float(data.iloc[-1]["atr"])
    current = float(data.iloc[-1]["close"])
    lookback = data.tail(30).reset_index(drop=True)
    zones = []

    for i in range(2, len(lookback)):
        c0 = lookback.iloc[i - 2]
        c2 = lookback.iloc[i]
        if float(c2["low"]) > float(c0["high"]):
            zones.append({"type": "bullish_fvg", "low": float(c0["high"]), "high": float(c2["low"])})
        if float(c2["high"]) < float(c0["low"]):
            zones.append({"type": "bearish_fvg", "low": float(c2["high"]), "high": float(c0["low"])})

    for zone in reversed(zones):
        if direction == "long" and zone["type"] == "bullish_fvg":
            near = zone["low"] - atr * 0.25 <= current <= zone["high"] + atr * 0.75
            return {
                "ok": near,
                "event": "bullish_fvg",
                "low": round(zone["low"], 3),
                "high": round(zone["high"], 3),
            }
        if direction == "short" and zone["type"] == "bearish_fvg":
            near = zone["low"] - atr * 0.75 <= current <= zone["high"] + atr * 0.25
            return {
                "ok": near,
                "event": "bearish_fvg",
                "low": round(zone["low"], 3),
                "high": round(zone["high"], 3),
            }

    return {"ok": False, "event": "none"}


def order_block_proxy(data, direction: str) -> dict:
    atr = float(data.iloc[-1]["atr"])
    current = float(data.iloc[-1]["close"])
    candles = data.tail(18).reset_index(drop=True)

    for i in range(len(candles) - 2, 1, -1):
        candle = candles.iloc[i]
        nxt = candles.iloc[i + 1]
        if direction == "long":
            opposite = float(candle["close"]) < float(candle["open"])
            impulse = float(nxt["close"]) - float(candle["close"]) > atr * 0.6
            if opposite and impulse:
                low = float(candle["low"])
                high = float(candle["high"])
                near = low - atr * 0.25 <= current <= high + atr * 0.75
                return {"ok": near, "event": "bullish_ob", "low": round(low, 3), "high": round(high, 3)}
        if direction == "short":
            opposite = float(candle["close"]) > float(candle["open"])
            impulse = float(candle["close"]) - float(nxt["close"]) > atr * 0.6
            if opposite and impulse:
                low = float(candle["low"])
                high = float(candle["high"])
                near = low - atr * 0.75 <= current <= high + atr * 0.25
                return {"ok": near, "event": "bearish_ob", "low": round(low, 3), "high": round(high, 3)}

    return {"ok": False, "event": "none"}


def wyckoff_trap(data, direction: str) -> dict:
    recent = data.tail(12)
    prior = data.iloc[-32:-12]
    if prior.empty:
        return {"ok": False, "event": "none"}

    prior_low = float(prior["low"].min())
    prior_high = float(prior["high"].max())
    last = data.iloc[-1]
    atr = float(last["atr"])
    spring = float(recent["low"].min()) < prior_low - atr * 0.1 and float(last["close"]) > prior_low
    upthrust = float(recent["high"].max()) > prior_high + atr * 0.1 and float(last["close"]) < prior_high

    if direction == "long" and spring:
        return {"ok": True, "event": "wyckoff_spring"}
    if direction == "short" and upthrust:
        return {"ok": True, "event": "wyckoff_upthrust"}
    return {"ok": False, "event": "none"}


def fibo_zone(data, direction: str, swing_high: float, swing_low: float, close: float) -> dict:
    swing_range = max(swing_high - swing_low, 0.000001)
    if direction == "long":
        retracement = (swing_high - close) / swing_range
    elif direction == "short":
        retracement = (close - swing_low) / swing_range
    else:
        retracement = 999

    in_golden_zone = 0.382 <= retracement <= 0.618
    near_breakout = retracement < 0.2
    return {
        "ok": in_golden_zone or near_breakout,
        "retracement": round(retracement, 3),
        "zone": "golden" if in_golden_zone else "breakout" if near_breakout else "none",
    }


def structure_levels(data, direction: str, swing_high: float, swing_low: float, close: float) -> dict:
    swing_range = max(swing_high - swing_low, 0.000001)
    levels = {
        "support": round(swing_low, 3),
        "resistance": round(swing_high, 3),
        "mid": round(swing_low + swing_range * 0.5, 3),
        "range": round(swing_range, 3),
    }
    if direction == "long":
        levels.update(
            {
                "fib_382": round(swing_high - swing_range * 0.382, 3),
                "fib_500": round(swing_high - swing_range * 0.5, 3),
                "fib_618": round(swing_high - swing_range * 0.618, 3),
                "preferred_zone": "buy pullback 38.2-61.8 or wait sweep/CHoCH",
            }
        )
    elif direction == "short":
        levels.update(
            {
                "fib_382": round(swing_low + swing_range * 0.382, 3),
                "fib_500": round(swing_low + swing_range * 0.5, 3),
                "fib_618": round(swing_low + swing_range * 0.618, 3),
                "preferred_zone": "sell pullback 38.2-61.8 or wait sweep/CHoCH",
            }
        )
    else:
        levels.update(
            {
                "fib_382": round(swing_low + swing_range * 0.382, 3),
                "fib_500": round(swing_low + swing_range * 0.5, 3),
                "fib_618": round(swing_low + swing_range * 0.618, 3),
                "preferred_zone": "wait for structure direction",
            }
        )
    return levels


def price_location(direction: str, swing_high: float, swing_low: float, close: float) -> dict:
    swing_range = max(swing_high - swing_low, 0.000001)
    position = (close - swing_low) / swing_range
    if direction == "long":
        chase = position > 0.82
        discount = position <= 0.62
    elif direction == "short":
        chase = position < 0.18
        discount = position >= 0.38
    else:
        chase = False
        discount = False
    return {"position": round(position, 3), "chase": chase, "discount": discount}
