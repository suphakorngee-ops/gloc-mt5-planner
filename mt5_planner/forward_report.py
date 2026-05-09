from collections import defaultdict
from datetime import datetime
import json


def build_forward_report(rows: list[dict], target_signals: int = 50, start_at: str | None = None) -> str:
    forward_rows = [row for row in rows if (row.get("source") or "forward") == "forward"]
    if start_at:
        start = parse_time(start_at)
        if start:
            forward_rows = [row for row in forward_rows if row_time(row) and row_time(row) >= start]
    lines = []
    lines.append("FORWARD TEST REPORT")
    lines.append("=" * 72)
    if start_at:
        lines.append(f"start_at: {start_at}")
    if not forward_rows:
        lines.append("no forward signals yet")
        lines.append(f"progress: 0/{target_signals}")
        lines.append("status: collect more signals before judging strategy")
        return "\n".join(lines)

    total = len(forward_rows)
    idea_rows = group_trade_ideas(forward_rows)
    wins = [row for row in forward_rows if row.get("status") in ("tp", "tp1")]
    losses = [row for row in forward_rows if row.get("status") == "sl"]
    open_rows = [row for row in forward_rows if row.get("status") == "open"]
    timeout_rows = [row for row in forward_rows if row.get("status") == "timeout"]
    be_rows = [row for row in forward_rows if row.get("status") == "be"]
    closed = len(wins) + len(losses)
    win_rate = len(wins) / closed * 100 if closed else 0
    r_values = [r_multiple(row) for row in forward_rows]
    r_values = [value for value in r_values if value is not None]
    expectancy = sum(r_values) / len(r_values) if r_values else 0
    gross_win = sum(value for value in r_values if value > 0)
    gross_loss = abs(sum(value for value in r_values if value < 0))
    profit_factor = gross_win / gross_loss if gross_loss else 0
    avg_risk = average([row.get("actual_risk_usd") for row in forward_rows])
    avg_win_r = average([value for value in r_values if value > 0])
    avg_loss_r = average([abs(value) for value in r_values if value < 0])
    remaining_50 = max(50 - total, 0)
    remaining_100 = max(100 - total, 0)

    lines.append(f"signals: {total}")
    if len(idea_rows) != total:
        idea_wins = [row for row in idea_rows if row.get("status") in ("tp", "tp1")]
        idea_losses = [row for row in idea_rows if row.get("status") == "sl"]
        idea_closed = len(idea_wins) + len(idea_losses)
        idea_wr = len(idea_wins) / idea_closed * 100 if idea_closed else 0
        lines.append(
            f"trade ideas: {len(idea_rows)} grouped from {total} raw signals | "
            f"wins {len(idea_wins)} | losses {len(idea_losses)} | closed WR {idea_wr:.1f}%"
        )
    lines.append(f"wins: {len(wins)} | losses: {len(losses)} | open: {len(open_rows)} | timeout: {len(timeout_rows)} | be: {len(be_rows)}")
    lines.append(f"closed win rate: {win_rate:.1f}%")
    lines.append(f"expectancy: {expectancy:.3f}R/signal | profit factor: {profit_factor:.2f}")
    lines.append(f"avg win: {avg_win_r:.2f}R | avg loss: -{avg_loss_r:.2f}R | avg $risk: {avg_risk:.2f}")
    lines.append(f"progress: {total}/50 ({remaining_50} left) | {total}/100 ({remaining_100} left)")
    lines.append(f"decision: {decision_text(total, expectancy, profit_factor, closed)}")
    lines.append("")
    lines.extend(group_section(forward_rows, "session"))
    lines.append("")
    lines.extend(group_section(forward_rows, "mode"))
    lines.append("")
    lines.extend(recent_section(forward_rows))
    return "\n".join(lines)


def group_trade_ideas(rows: list[dict], window_seconds: int = 600) -> list[dict]:
    groups = []
    for row in rows:
        created = row_time(row)
        key = row_idea_key(row)
        matched = None
        for group in reversed(groups):
            if group["key"] != key:
                continue
            if not created or not group["last_time"]:
                continue
            delta = abs((created - group["last_time"]).total_seconds())
            if delta <= window_seconds:
                matched = group
                break
        if not matched:
            matched = {
                "key": key,
                "first": row,
                "last_time": created,
                "rows": [],
            }
            groups.append(matched)
        matched["rows"].append(row)
        matched["last_time"] = created or matched["last_time"]

    return [combine_group(group["rows"]) for group in groups]


def combine_group(rows: list[dict]) -> dict:
    result = dict(rows[0])
    statuses = [row.get("status") for row in rows]
    if "tp" in statuses:
        winner = next(row for row in rows if row.get("status") == "tp")
        result.update({"status": "tp", "close_price": winner.get("close_price"), "closed_at": winner.get("closed_at")})
    elif "tp1" in statuses:
        winner = next(row for row in rows if row.get("status") == "tp1")
        result.update({"status": "tp1", "close_price": winner.get("close_price"), "closed_at": winner.get("closed_at")})
    elif all(status == "sl" for status in statuses):
        loser = rows[0]
        result.update({"status": "sl", "close_price": loser.get("close_price"), "closed_at": loser.get("closed_at")})
    elif "open" in statuses:
        result["status"] = "open"
    elif "timeout" in statuses:
        result["status"] = "timeout"
    elif "be" in statuses:
        result["status"] = "be"
    return result


def row_idea_key(row: dict) -> str:
    if row.get("idea_key"):
        return str(row["idea_key"])
    payload = row.get("payload")
    setup = "-"
    if payload:
        try:
            setup = json.loads(payload).get("setup") or "-"
        except (TypeError, ValueError, json.JSONDecodeError):
            setup = "-"
    return "|".join(
        [
            str(row.get("mode") or "-"),
            str(row.get("direction") or "-"),
            setup,
        ]
    )


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def row_time(row: dict) -> datetime | None:
    value = row.get("created_at")
    if not value:
        return None
    return parse_time(value)


def r_multiple(row: dict) -> float | None:
    try:
        entry = float(row.get("entry") or 0)
        stop = float(row.get("stop_loss") or 0)
    except (TypeError, ValueError):
        return None

    risk = abs(entry - stop)
    if risk <= 0:
        return None

    status = row.get("status")
    if status == "sl":
        return -1.0
    if status in ("open", "timeout", "be"):
        return 0.0
    if status not in ("tp", "tp1"):
        return None

    try:
        close = float(row.get("close_price") or 0)
    except (TypeError, ValueError):
        return None
    if close <= 0:
        return None

    if row.get("direction") == "long":
        return (close - entry) / risk
    if row.get("direction") == "short":
        return (entry - close) / risk
    return None


def average(values) -> float:
    parsed = []
    for value in values:
        try:
            parsed.append(float(value))
        except (TypeError, ValueError):
            pass
    return sum(parsed) / len(parsed) if parsed else 0.0


def decision_text(total: int, expectancy: float, profit_factor: float, closed: int) -> str:
    if total < 50:
        return "WAIT - collect at least 50 forward signals"
    if closed < 30:
        return "WAIT - not enough closed results"
    if expectancy <= 0 or profit_factor < 1.3:
        return "NO AUTO - forward edge not confirmed"
    if total < 100:
        return "WATCH - positive, but collect toward 100 before auto"
    return "DEMO AUTO CANDIDATE - still require daily loss and max trade guards"


def group_section(rows: list[dict], field: str) -> list[str]:
    grouped = defaultdict(lambda: {"tp": 0, "tp1": 0, "be": 0, "sl": 0, "timeout": 0, "open": 0})
    for row in rows:
        key = row.get(field) or "-"
        status = row.get("status") or "open"
        grouped[key][status] += 1

    lines = [field.upper(), f"{field:<14} {'win':>5} {'sl':>5} {'open':>6} {'timeout':>8} {'wr':>8}"]
    for key, counts in sorted(grouped.items()):
        win = counts["tp"] + counts["tp1"]
        loss = counts["sl"]
        closed = win + loss
        wr = win / closed * 100 if closed else 0
        lines.append(f"{key:<14} {win:>5} {loss:>5} {counts['open']:>6} {counts['timeout']:>8} {wr:>7.1f}%")
    return lines


def recent_section(rows: list[dict], limit: int = 10) -> list[str]:
    recent = rows[-limit:]
    lines = ["RECENT", f"{'created_at':<28} {'side':<6} {'status':<8} {'entry':>10} {'sl':>10} {'tp':>10}"]
    for row in recent:
        lines.append(
            f"{row.get('created_at', '-'):<28} {row.get('direction', '-'):<6} "
            f"{row.get('status', '-'):<8} {float(row.get('entry') or 0):>10.3f} "
            f"{float(row.get('stop_loss') or 0):>10.3f} {float(row.get('take_profit') or 0):>10.3f}"
        )
    return lines
