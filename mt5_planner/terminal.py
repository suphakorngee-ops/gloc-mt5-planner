import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_report(
    symbol: str,
    timeframe: str,
    df,
    plans: list[dict],
    saved_count: int = 0,
    tracker_count: int = 0,
    spread: dict | None = None,
    quality: dict | None = None,
    session: str | None = None,
    block_reason: str | None = None,
    strategy_block_reason: str | None = None,
    features: dict | None = None,
) -> None:
    last = df.dropna().iloc[-1]
    candle_time = last["time"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    width = 96
    print("═" * width)
    session_text = f" | session {session}" if session else ""
    print(f"📊 {symbol} {timeframe} | updated {now} | candle {candle_time}{session_text}")
    print("═" * width)
    print("💹 MARKET")
    line = (
        f"price {last['close']:.3f} | rsi {last['rsi']:.1f} | atr {last['atr']:.3f}"
    )
    if spread and spread.get("available"):
        line += f" | spread {spread['spread']:.3f}"
    print(line)
    if quality:
        print(f"⭐ quality {quality['label']} / {quality['score']} | {quality['notes']}")
    if features and features.get("ok"):
        print("─" * width)
        print("🧱 STRUCTURE")
        print(
            f"bias={features['direction']} | strength={features['trend_follow']['strength']} | "
            f"scalp={features['scalp_momentum']['ok']} | loc={features['location']['position']} | "
            f"zone={zone_label(features)}"
        )
        print(
            f"smc={features['smc']['event']} | flow={features['smc_flow']['event']} | "
            f"fibo={features['fibo']['zone']} retrace={features['fibo']['retracement']}"
        )
        print_levels(features, width)
    else:
        print(f"swing_low {last['swing_low']:.3f} | swing_high {last['swing_high']:.3f}")
    print("─" * width)
    print("🧪 mode: FORWARD TEST | paper signal tracked even if skipped | real execution: manual only")
    print("─" * width)

    if not plans:
        if spread and not spread.get("ok", True):
            status = "SPREAD BLOCK"
            reason = spread["reason"]
        elif block_reason:
            status = "QUALITY BLOCK"
            reason = block_reason
        else:
            status = "NO TRADE"
            reason = strategy_block_reason or "trend filter not confirmed or momentum not enough"
        print(f"🚦 STATUS: {status}")
        print(f"📝 reason: {reason}")
        if features and features.get("ok"):
            print_wait_hint(reason, features, width)
        print("═" * width)
        return

    print("🎯 TRADE PLAN")
    print(
        f"{'mode':<12} {'side':<6} {'entry':>10} {'sl':>10} {'tp':>10} "
        f"{'rr':>6} {'risk':>8} {'$risk':>8} {'lot':>6}"
    )
    print("─" * width)
    for plan in plans:
        print(
            f"{plan['mode']:<12} {plan['direction']:<6} "
            f"{plan['entry']:>10.3f} {plan['stop_loss']:>10.3f} "
            f"{plan['take_profit']:>10.3f} {plan['risk_reward']:>6.2f} "
            f"{plan['risk_pct']:>7.2%} {plan['actual_risk_usd']:>8.2f} "
            f"{plan['lot']:>6.2f}"
        )

    print("─" * width)
    setup_text = f" | setup {plans[0].get('setup', '-')}" if plans else ""
    print(
        f"🧭 bias: {plans[0]['direction'].upper()} | "
        f"saved_new_signals: {saved_count} | tracker_updates: {tracker_count}{setup_text}"
    )
    print(f"📝 reason: {plans[0]['reason']}")
    valid_for = plans[0].get("valid_for_bars")
    if valid_for:
        print(f"⏳ trade note: optional demo only; do not chase after {valid_for} closed candles")
    fixed = [plan["mode"] for plan in plans if plan.get("risk_note") == "fixed_lot"]
    risky = [plan["mode"] for plan in plans if plan.get("risk_note") == "min_lot_exceeds_target_risk"]
    if fixed:
        print(f"📌 note: fixed lot is used for {', '.join(fixed)}; check $risk before entering")
    if risky:
        print(f"⚠️ note: min lot makes actual risk higher than target for {', '.join(risky)}")
    risk_warnings = [f"{plan['mode']}: {plan['risk_warning']}" for plan in plans if plan.get("risk_warning")]
    if risk_warnings:
        print(f"⚠️ risk warning: {' | '.join(risk_warnings)}")
    print("═" * width)


def print_levels(features: dict, width: int) -> None:
    levels = features.get("levels") or {}
    if not levels:
        return
    print("─" * width)
    print("📍 LEVELS")
    print(
        f"🟢 support {levels['support']:.3f} | ⚪ mid {levels['mid']:.3f} | "
        f"🔴 resistance {levels['resistance']:.3f} | range {levels['range']:.3f}"
    )
    print(
        f"📐 fibo 38.2 {levels['fib_382']:.3f} | 50.0 {levels['fib_500']:.3f} | "
        f"61.8 {levels['fib_618']:.3f}"
    )
    print(f"👀 watch: {levels['preferred_zone']}")


def zone_label(features: dict) -> str:
    loc = (features.get("location") or {}).get("position")
    if loc is None:
        return "-"
    if loc <= 0.2:
        return "near support / sell chase risk"
    if loc >= 0.8:
        return "near resistance / buy chase risk"
    if 0.382 <= loc <= 0.618:
        return "middle / fib value zone"
    return "normal"


def print_wait_hint(reason: str, features: dict, width: int) -> None:
    levels = features.get("levels") or {}
    direction = features.get("direction")
    print("─" * width)
    print("⏳ WAIT PLAN")
    if "near swing high" in reason and levels:
        print(f"price is high in range; wait pullback toward {levels['fib_382']:.3f}-{levels['fib_618']:.3f} or sweep/CHoCH")
    elif "near swing low" in reason and levels:
        print(f"price is low in range; wait pullback toward {levels['fib_382']:.3f}-{levels['fib_618']:.3f} or sweep/CHoCH")
    elif "setup not in allowlist" in reason or "waiting" in reason:
        print("wait for stronger confirmation: retest, VCP/BOS, liquidity sweep, CHoCH, FVG or OB")
    elif direction == "neutral":
        print("wait for clear BOS/sweep before choosing buy or sell")
    else:
        print("skip this candle; wait for cleaner location and confirmation")
