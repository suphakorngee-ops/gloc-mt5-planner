from .indicators import add_indicators
from .strategy import analyze_trade
from .spread_filter import spread_status
from .quality import market_quality, session_label
from .market_features import compute_market_features
from .tracker import mfe_mae_for_signal
from .session_rules import session_profile


def run_backtest(raw_df, config: dict, progress: bool = False) -> list[dict]:
    settings = config.get("strategy", {})
    min_bars = int(config.get("backtest", {}).get("min_bars", 220))
    max_hold_bars = int(config.get("backtest", {}).get("max_hold_bars", 48))
    results = []
    indicator_df = add_indicators(raw_df, settings).dropna().reset_index(drop=True)

    total = max(len(indicator_df) - 2 - min_bars, 1)
    last_percent = -1

    for index in range(min_bars, len(indicator_df) - 2):
        if progress:
            done = index - min_bars
            percent = int(done / total * 100)
            if percent >= last_percent + 5:
                print(f"backtest progress: {percent}% ({done}/{total})")
                last_percent = percent
        df = indicator_df.iloc[: index + 1].copy()
        if len(df) < min_bars / 2:
            continue

        analysis = analyze_trade(df, config)
        plans = analysis["plans"]
        spread = spread_status(df, config)
        if not spread["ok"]:
            continue

        features = compute_market_features(df, analysis.get("direction"))
        quality = market_quality(df.iloc[-1], spread, features)
        if quality_blocked(config, quality):
            continue

        session = session_label(df.iloc[-1]["time"])
        profile = session_profile(session, config)
        hold_bars = int(profile.get("max_hold_bars", max_hold_bars))
        future = indicator_df.iloc[index + 1 : index + 1 + hold_bars].copy()
        for plan in plans:
            enriched = enrich_plan(plan, quality, session, spread, features)
            row = plan_to_row(enriched)
            result = first_hit_with_management(row, future, profile)
            mfe_mae = mfe_mae_for_signal(row, future)
            row.update(
                {
                    "status": result["status"] if result else "timeout",
                    "closed_at": str(result["time"]) if result else None,
                    "close_price": result["price"] if result else None,
                    "mfe": mfe_mae["mfe"],
                    "mae": mfe_mae["mae"],
                }
            )
            results.append(row)

    if progress:
        print(f"backtest progress: 100% ({total}/{total})")
    return results


def first_hit_with_management(row: dict, future, profile: dict) -> dict | None:
    entry = float(row["entry"])
    stop = float(row["stop_loss"])
    target = float(row["take_profit"])
    direction = row["direction"]
    risk = abs(entry - stop)
    if risk <= 0:
        return None

    tp1_rr = float(profile.get("tp1_rr", 1.0))
    move_be_rr = float(profile.get("move_be_at_rr", 1.0))
    be_armed = False
    if direction == "long":
        tp1 = entry + risk * tp1_rr
        be_trigger = entry + risk * move_be_rr
        for _, candle in future.iterrows():
            high = float(candle["high"])
            low = float(candle["low"])
            hit_sl = low <= stop
            hit_tp1 = high >= tp1
            hit_be_trigger = high >= be_trigger
            hit_tp = high >= target
            if hit_sl and hit_tp:
                return {"status": "ambiguous", "time": candle["time"], "price": float(candle["close"])}
            if hit_sl and not be_armed:
                return {"status": "sl", "time": candle["time"], "price": stop}
            if hit_tp1:
                return {"status": "tp1", "time": candle["time"], "price": tp1}
            if hit_be_trigger:
                be_armed = True
            if hit_tp:
                return {"status": "tp", "time": candle["time"], "price": target}
            if be_armed and low <= entry:
                return {"status": "be", "time": candle["time"], "price": entry}
    else:
        tp1 = entry - risk * tp1_rr
        be_trigger = entry - risk * move_be_rr
        for _, candle in future.iterrows():
            high = float(candle["high"])
            low = float(candle["low"])
            hit_sl = high >= stop
            hit_tp1 = low <= tp1
            hit_be_trigger = low <= be_trigger
            hit_tp = low <= target
            if hit_sl and hit_tp:
                return {"status": "ambiguous", "time": candle["time"], "price": float(candle["close"])}
            if hit_sl and not be_armed:
                return {"status": "sl", "time": candle["time"], "price": stop}
            if hit_tp1:
                return {"status": "tp1", "time": candle["time"], "price": tp1}
            if hit_be_trigger:
                be_armed = True
            if hit_tp:
                return {"status": "tp", "time": candle["time"], "price": target}
            if be_armed and high >= entry:
                return {"status": "be", "time": candle["time"], "price": entry}
    return None


def quality_blocked(config: dict, quality: dict) -> bool:
    min_score = int(config.get("quality_filter", {}).get("min_score", 0))
    return bool(min_score and int(quality["score"]) < min_score)


def enrich_plan(plan: dict, quality: dict, session: str, spread: dict, features: dict) -> dict:
    enriched = dict(plan)
    enriched["quality_score"] = quality["score"]
    enriched["quality_label"] = quality["label"]
    enriched["quality_notes"] = quality["notes"]
    enriched["session"] = session
    enriched["features"] = features
    if spread.get("available"):
        enriched["spread"] = spread["spread"]
    return enriched


def plan_to_row(plan: dict) -> dict:
    features = plan.get("features") or {}
    smc_flow = features.get("smc_flow") or {}
    fvg = smc_flow.get("fvg") or {}
    order_block = smc_flow.get("order_block") or {}
    wyckoff = smc_flow.get("wyckoff") or {}
    fibo = features.get("fibo") or {}
    return {
        "created_at": plan.get("candle_time"),
        "symbol": "",
        "timeframe": "",
        "mode": plan["mode"],
        "direction": plan["direction"],
        "entry": plan["entry"],
        "stop_loss": plan["stop_loss"],
        "take_profit": plan["take_profit"],
        "risk_reward": plan["risk_reward"],
        "quality_score": plan.get("quality_score"),
        "quality_label": plan.get("quality_label"),
        "session": plan.get("session"),
        "spread": plan.get("spread"),
        "lot": plan.get("lot"),
        "actual_risk_usd": plan.get("actual_risk_usd"),
        "setup": plan.get("setup"),
        "scalp_momentum": (features.get("scalp_momentum") or {}).get("ok"),
        "trend_strength": (features.get("trend_follow") or {}).get("strength"),
        "smc_event": (features.get("smc") or {}).get("event"),
        "smc_flow": smc_flow.get("event"),
        "fvg_event": fvg.get("event"),
        "order_block": order_block.get("event"),
        "wyckoff_event": wyckoff.get("event"),
        "fibo_zone": fibo.get("zone"),
        "fibo_retracement": fibo.get("retracement"),
        "payload": plan,
    }
