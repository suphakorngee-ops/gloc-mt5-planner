from datetime import datetime
from pathlib import Path
from urllib import request
import json
import os


ROUTE_ENV = {
    "signals": "MT5_PLANNER_DISCORD_SIGNALS_WEBHOOK",
    "reports": "MT5_PLANNER_DISCORD_REPORTS_WEBHOOK",
    "ops": "MT5_PLANNER_DISCORD_OPS_WEBHOOK",
}


def emit_signal_alert(symbol: str, timeframe: str, plans: list[dict], saved_count: int, config: dict) -> None:
    if saved_count <= 0 or not plans:
        return

    settings = config.get("alerts", {})
    if settings.get("enabled", True) is False:
        return

    report_dir = Path(settings.get("dir", "reports"))
    report_dir.mkdir(parents=True, exist_ok=True)
    selected = plans[:saved_count]
    lines = [format_signal_message(symbol, timeframe, plan) for plan in selected]

    if settings.get("beep", True):
        print("\a", end="")
    if settings.get("print", True):
        print("NEW SIGNAL")
        for line in lines:
            print(line)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [compact_signal_line(symbol, timeframe, plan) for plan in selected]
    with (report_dir / "alerts.log").open("a", encoding="utf-8") as file:
        for line in log_lines:
            file.write(f"{timestamp} | {line}\n")
    (report_dir / "latest_signal.txt").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    with (report_dir / "signal_inbox.txt").open("a", encoding="utf-8") as file:
        file.write(f"\n[{timestamp}] NEW SAVED SIGNAL\n")
        for line in lines:
            file.write(f"{line}\n\n")
    (report_dir / "latest_signal.json").write_text(
        json.dumps(
            {"symbol": symbol, "timeframe": timeframe, "plans": selected, "saved_at": timestamp},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    send_discord_signal(settings, symbol, timeframe, selected, title="NEW PAPER SIGNAL")


def resend_latest_signal(config: dict) -> str:
    settings = config.get("alerts", {})
    report_dir = Path(settings.get("dir", "reports"))
    latest_json = report_dir / "latest_signal.json"
    if latest_json.exists():
        payload = json.loads(latest_json.read_text(encoding="utf-8"))
        send_discord_signal(
            settings,
            payload.get("symbol", config.get("symbol", "symbol")),
            payload.get("timeframe", config.get("timeframe", "M5")),
            payload.get("plans", []),
            title="RESEND LATEST SIGNAL",
        )
        return "latest signal resent if Discord webhook is configured"

    latest = report_dir / "latest_signal.txt"
    if not latest.exists():
        return f"latest signal not found: {latest}"
    content = latest.read_text(encoding="utf-8").strip()
    if not content:
        return f"latest signal is empty: {latest}"
    send_discord_alert(settings, [content], route="signals", title="RESEND LATEST SIGNAL")
    return "latest signal resent if Discord webhook is configured"


def format_signal_message(symbol: str, timeframe: str, plan: dict) -> str:
    direction = str(plan["direction"]).upper()
    side_icon = "🟢" if direction == "LONG" else "🔴"
    risk = float(plan.get("actual_risk_usd", 0) or 0)
    score = plan.get("quality_score")
    quality = plan.get("quality_label") or "-"
    quality_text = f"{quality}{score}" if score is not None else quality
    setup = plan.get("setup") or "-"
    session = plan.get("session") or "-"
    valid = plan.get("valid_for_bars", "-")
    rr = float(plan.get("risk_reward", 0) or 0)
    lot = float(plan.get("lot", 0) or 0)
    reason = shorten(plan.get("reason") or plan.get("setup_reason") or "-", 260)
    notes = shorten(", ".join(plan.get("quality_notes") or []), 220)
    idea = plan.get("idea_key") or "-"
    return (
        f"{side_icon} **{symbol} {timeframe}** | `{plan['mode']}` `{direction}` | `{session}`\n"
        f"🎯 **Entry** `{plan['entry']:.3f}`\n"
        f"🛑 **SL** `{plan['stop_loss']:.3f}`  ✅ **TP** `{plan['take_profit']:.3f}`\n"
        f"⚖️ **RR** `{rr:.2f}`  📦 **Lot** `{lot:.2f}`  💵 **Risk** `${risk:.2f}`\n"
        f"⭐ **Quality** `{quality_text}`  ⏳ **Valid** `{valid}` M5 bars\n"
        f"🧩 **Setup** `{setup}`\n"
        f"🧠 **Why** {reason}\n"
        f"📝 **Notes** {notes}\n"
        f"🔑 **Idea** `{idea}`"
    )


def compact_signal_line(symbol: str, timeframe: str, plan: dict) -> str:
    return (
        f"{symbol} {timeframe} | {plan['mode']} {str(plan['direction']).upper()} | "
        f"entry {plan['entry']:.3f} | sl {plan['stop_loss']:.3f} | "
        f"tp {plan['take_profit']:.3f} | rr {plan['risk_reward']:.2f} | "
        f"lot {plan.get('lot', 0):.2f} | $risk {plan.get('actual_risk_usd', 0):.2f}"
    )


def send_discord_alert(
    settings: dict,
    lines: list[str],
    *,
    route: str = "signals",
    title: str = "GLOC UPDATE",
) -> None:
    discord = settings.get("discord", {})
    if not discord.get("enabled", False):
        return

    webhook_url = discord_webhook_url(discord, route)
    if not webhook_url:
        print(f"Discord alert skipped: webhook missing for {route}")
        return

    content = format_discord_message(lines, route=route, title=title)
    payload = {"content": content[:1900]}
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "MT5-Planner"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status >= 300:
                print(f"Discord alert failed: HTTP {response.status}")
    except Exception as exc:
        print(f"Discord alert failed: {exc}")


def send_discord_signal(settings: dict, symbol: str, timeframe: str, plans: list[dict], *, title: str) -> None:
    discord = settings.get("discord", {})
    if not discord.get("enabled", False):
        return

    webhook_url = discord_webhook_url(discord, "signals")
    if not webhook_url:
        print("Discord signal skipped: webhook missing for signals")
        return

    payload = {
        "content": f"🚨 **{title}**\n📌 Paper/manual only | Auto execution OFF",
        "embeds": [signal_embed(symbol, timeframe, plan) for plan in plans[:10]],
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "MT5-Planner"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status >= 300:
                print(f"Discord signal failed: HTTP {response.status}")
    except Exception as exc:
        print(f"Discord signal failed: {exc}")


def signal_embed(symbol: str, timeframe: str, plan: dict) -> dict:
    direction = str(plan.get("direction", "-")).upper()
    color = 0x2ECC71 if direction == "LONG" else 0xE74C3C
    score = plan.get("quality_score")
    quality = plan.get("quality_label") or "-"
    quality_text = f"{quality}{score}" if score is not None else quality
    risk = float(plan.get("actual_risk_usd", 0) or 0)
    rr = float(plan.get("risk_reward", 0) or 0)
    lot = float(plan.get("lot", 0) or 0)
    setup = shorten(plan.get("setup") or "-", 180)
    reason = shorten(plan.get("reason") or plan.get("setup_reason") or "-", 260)
    notes = shorten(", ".join(plan.get("quality_notes") or []), 220)
    return {
        "title": f"{symbol} {timeframe} | {plan.get('mode', '-')} {direction}",
        "description": f"Session: `{plan.get('session') or '-'}` | Valid: `{plan.get('valid_for_bars', '-')}` M5 bars",
        "color": color,
        "fields": [
            {"name": "Entry", "value": f"`{float(plan.get('entry', 0)):.3f}`", "inline": True},
            {"name": "SL", "value": f"`{float(plan.get('stop_loss', 0)):.3f}`", "inline": True},
            {"name": "TP", "value": f"`{float(plan.get('take_profit', 0)):.3f}`", "inline": True},
            {"name": "RR", "value": f"`{rr:.2f}`", "inline": True},
            {"name": "Lot", "value": f"`{lot:.2f}`", "inline": True},
            {"name": "Risk", "value": f"`${risk:.2f}`", "inline": True},
            {"name": "Quality", "value": f"`{quality_text}`", "inline": True},
            {"name": "Setup", "value": f"`{setup}`", "inline": False},
            {"name": "Why", "value": reason, "inline": False},
            {"name": "Notes", "value": notes or "-", "inline": False},
            {"name": "Idea", "value": f"`{shorten(plan.get('idea_key') or '-', 180)}`", "inline": False},
        ],
        "footer": {"text": "Gloc MT5 Planner | paper/manual only | auto execution OFF"},
    }


def discord_webhook_url(discord: dict, route: str) -> str:
    webhooks = discord.get("webhooks", {})
    return (
        webhooks.get(route)
        or os.environ.get(ROUTE_ENV.get(route, ""))
        or discord.get("webhook_url")
        or os.environ.get("MT5_PLANNER_DISCORD_WEBHOOK")
        or ""
    )


def format_discord_message(lines: list[str], *, route: str, title: str) -> str:
    route_icon = {"signals": "🚨", "reports": "📊", "ops": "🛠️"}.get(route, "📌")
    header = f"{route_icon} **{title}**\n📌 Paper/manual only | Auto execution OFF"
    divider = "━━━━━━━━━━━━━━━━━━━━"
    return "\n\n".join([header, divider, *lines])


def shorten(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
