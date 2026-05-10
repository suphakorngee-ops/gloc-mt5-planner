from .daily_report import build_daily_report
from .execution import execution_status
from .forward_report import build_forward_report
from .journal import Journal
from .order_ledger import build_order_report


HELP_TEXT = """Gloc read-only commands:
/status
/report [btc|xau|all]
/daily [btc|xau|all]
/latest
/execution-status [btc|xau|all]
/orders [btc|xau|all]
/lesson

Order execution commands are intentionally unavailable."""


def build_discord_reply(message: str, configs: list[dict]) -> str:
    text = (message or "").strip()
    if not text:
        return HELP_TEXT

    parts = text.split()
    command = parts[0].lower()
    target = parts[1].lower() if len(parts) > 1 else "all"

    if command in ("/help", "help"):
        return HELP_TEXT
    if command == "/status":
        return status_reply(configs)
    if command == "/latest":
        return latest_reply()
    if command == "/report":
        return joined_symbol_reply(configs, target, forward_reply)
    if command == "/daily":
        return joined_symbol_reply(configs, target, daily_reply)
    if command in ("/execution-status", "/execution"):
        return joined_symbol_reply(configs, target, execution_reply)
    if command in ("/orders", "/order-report"):
        return joined_symbol_reply(configs, target, order_reply)
    if command in ("/lesson", "/lessons"):
        return lesson_reply()

    return f"Unknown command: {command}\n\n{HELP_TEXT}"


def status_reply(configs: list[dict]) -> str:
    lines = ["Gloc MT5 Planner status"]
    for config in configs:
        journal = Journal(config.get("journal_path", "journal.sqlite"))
        start_at = config.get("report", {}).get("forward_start")
        forward = build_forward_report(journal.all_signals(), target_signals=50, start_at=start_at, config=config)
        picked = [
            line
            for line in forward.splitlines()
            if line.startswith(("raw signals:", "grouped trade ideas:", "execution:", "MT5 today/history:", "progress:", "decision:")) or line == "no forward signals yet"
        ]
        lines.append(f"{config['symbol']} {config['timeframe']}: " + " | ".join(picked[:3]))
    return trim_discord("\n".join(lines))


def joined_symbol_reply(configs: list[dict], target: str, builder) -> str:
    selected = [config for config in configs if matches_target(config, target)]
    if not selected:
        return "Unknown symbol. Use btc, xau, or all."
    return trim_discord("\n\n".join(builder(config) for config in selected))


def forward_reply(config: dict) -> str:
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    start_at = config.get("report", {}).get("forward_start")
    return build_forward_report(journal.all_signals(), target_signals=50, start_at=start_at, config=config)


def daily_reply(config: dict) -> str:
    journal = Journal(config.get("journal_path", "journal.sqlite"))
    start_at = config.get("report", {}).get("forward_start")
    return build_daily_report(journal.all_signals(), days=7, start_at=start_at)


def execution_reply(config: dict) -> str:
    return execution_status(config)


def order_reply(config: dict) -> str:
    start_at = config.get("report", {}).get("forward_start")
    return build_order_report(config, start_at=start_at)


def latest_reply() -> str:
    try:
        content = open("reports/latest_signal.txt", "r", encoding="utf-8").read().strip()
    except FileNotFoundError:
        return "No latest signal file yet."
    return content or "No latest signal yet."


def lesson_reply() -> str:
    chunks = []
    for path in ("TRADE_LESSONS.md", "SOUL.md"):
        try:
            content = open(path, "r", encoding="utf-8").read().strip()
        except FileNotFoundError:
            continue
        if content:
            chunks.append(f"## {path}\n{content}")
    return trim_discord("\n\n".join(chunks) or "No lesson files yet.")


def matches_target(config: dict, target: str) -> bool:
    if target == "all":
        return True
    symbol = str(config.get("symbol", "")).lower()
    return target in symbol


def trim_discord(text: str, limit: int = 1900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n...trimmed"
