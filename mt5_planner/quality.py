from .market_features import compute_market_features


def market_quality(last, spread: dict | None = None, features: dict | None = None) -> dict:
    score = 50
    notes = []

    atr = float(last["atr"])
    rsi = float(last["rsi"])
    price = float(last["close"])

    trend_strength = float((features or {}).get("trend_strength", 0))

    if trend_strength >= 3.0:
        score += 15
        notes.append("structure ok")
    elif trend_strength < 1.0:
        score -= 15
        notes.append("weak structure")

    if 52 <= rsi <= 68 or 32 <= rsi <= 48:
        score += 10
        notes.append("rsi usable")
    elif rsi > 75 or rsi < 25:
        score -= 15
        notes.append("rsi stretched")

    if atr / price >= 0.0005:
        score += 10
        notes.append("volatility ok")
    else:
        score -= 10
        notes.append("low volatility")

    if spread and spread.get("available") and atr > 0:
        spread_atr = float(spread["spread"]) / atr
        if spread_atr <= 0.15:
            score += 10
            notes.append("spread ok")
        else:
            score -= 20
            notes.append("spread heavy")

    if features and features.get("ok"):
        if features["scalp_momentum"]["ok"]:
            score += 8
            notes.append("scalp momentum")
        if features["trend_follow"]["ok"]:
            score += 8
            notes.append("structure follow")
        if features["smc"]["ok"]:
            score += 10
            notes.append(features["smc"]["event"])
        if features["smc_flow"]["ok"]:
            score += 15
            notes.append("smc flow")
        if features["fibo"]["ok"]:
            score += 8
            notes.append(f"fibo {features['fibo']['zone']}")

    score = max(0, min(100, score))
    label = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    return {"score": score, "label": label, "notes": ", ".join(notes)}


def session_label(candle_time) -> str:
    hour = candle_time.hour
    if 0 <= hour < 7:
        return "Asia"
    if 7 <= hour < 12:
        return "London AM"
    if 12 <= hour < 17:
        return "London/NY"
    if 17 <= hour < 22:
        return "NY"
    return "Late NY"
