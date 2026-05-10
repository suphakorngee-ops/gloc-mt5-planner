from datetime import datetime
from pathlib import Path
from urllib import request
import json
import os


ROUTE_ENV = {
    "signals": "MT5_PLANNER_DISCORD_SIGNALS_WEBHOOK",
    "reports": "MT5_PLANNER_DISCORD_REPORTS_WEBHOOK",
    "ops": "MT5_PLANNER_DISCORD_OPS_WEBHOOK",
    "chat": "MT5_PLANNER_DISCORD_CHAT_WEBHOOK",
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
    send_discord_signal(settings, symbol, timeframe, selected, title="NEW STRATEGY SIGNAL", config=config)


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
            config=config,
        )
        return "latest signal resent if Discord webhook is configured"

    latest = report_dir / "latest_signal.txt"
    if not latest.exists():
        return f"latest signal not found: {latest}"
    content = latest.read_text(encoding="utf-8").strip()
    if not content:
        return f"latest signal is empty: {latest}"
    send_discord_alert(
        settings,
        [content],
        route="signals",
        title="RESEND LATEST SIGNAL",
        status_text=discord_status_text(config),
    )
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
    notes = shorten(join_notes(plan.get("quality_notes")), 220)
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
    status_text: str | None = None,
) -> None:
    discord = settings.get("discord", {})
    if not discord.get("enabled", False):
        return

    webhook_url = discord_webhook_url(discord, route)
    if not webhook_url:
        print(f"Discord alert skipped: webhook missing for {route}")
        return

    content = format_discord_message(lines, route=route, title=title, status_text=status_text)
    payload = {"content": content[:1900]}
    if route == "chat":
        payload["thread_name"] = "gloc-chat"
    post_discord_payload(webhook_url, payload, "Discord alert")


def send_discord_signal(
    settings: dict,
    symbol: str,
    timeframe: str,
    plans: list[dict],
    *,
    title: str,
    config: dict | None = None,
) -> None:
    discord = settings.get("discord", {})
    if not discord.get("enabled", False):
        return

    webhook_url = discord_webhook_url(discord, "signals")
    if not webhook_url:
        print("Discord signal skipped: webhook missing for signals")
        return

    payload = {
        "content": f"🚨 **{title}**\n📌 {discord_status_text(config)}",
        "embeds": [signal_embed(symbol, timeframe, plan, config=config) for plan in plans[:10]],
    }
    post_discord_payload(webhook_url, payload, "Discord signal")


def signal_embed(symbol: str, timeframe: str, plan: dict, config: dict | None = None) -> dict:
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
    notes = shorten(join_notes(plan.get("quality_notes")), 220)
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
        "footer": {"text": f"Gloc MT5 Planner | {discord_status_text(config)}"},
    }


def post_discord_payload(webhook_url: str, payload: dict, label: str) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "MT5-Planner"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status >= 300:
                print(f"{label} failed: HTTP {response.status}")
    except Exception as exc:
        print(f"{label} failed: {exc}")


def discord_webhook_url(discord: dict, route: str) -> str:
    webhooks = discord.get("webhooks", {})
    return (
        webhooks.get(route)
        or os.environ.get(ROUTE_ENV.get(route, ""))
        or discord.get("webhook_url")
        or os.environ.get("MT5_PLANNER_DISCORD_WEBHOOK")
        or ""
    )


def format_discord_message(lines: list[str], *, route: str, title: str, status_text: str | None = None) -> str:
    route_icon = {"signals": "🚨", "reports": "📊", "ops": "🛠️", "chat": "💬"}.get(route, "📌")
    header = f"{route_icon} **{title}**\n📌 {status_text or 'Gloc local alert'}"
    divider = "━━━━━━━━━━━━━━━━━━━━"
    return "\n\n".join([header, divider, *lines])


def discord_status_text(config: dict | None) -> str:
    if not config:
        return "Gloc local alert"
    execution = config.get("execution", {})
    if not execution.get("enabled", False):
        return "Paper/forward tracking | execution OFF"
    if execution.get("dry_run", True):
        return "Demo validation only | dry run ON"
    if execution.get("mode") == "demo_auto" and execution.get("demo_only", True):
        max_open = execution.get("max_open_trades", 1)
        return f"BTC demo auto ON | guarded | max open {max_open}"
    return "Execution enabled | check config guards"


def join_notes(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def shorten(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
