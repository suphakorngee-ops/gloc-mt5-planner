from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .forward_report import r_multiple


def build_daily_report(rows: list[dict], days: int = 7, start_at: str | None = None) -> str:
    tz = ZoneInfo("Asia/Bangkok")
    now = datetime.now(tz)
    start_day = (now.date() - timedelta(days=max(days - 1, 0)))
    start_time = parse_time(start_at) if start_at else None
    forward_rows = [row for row in rows if (row.get("source") or "forward") == "forward"]
    if start_time:
        forward_rows = [row for row in forward_rows if row_time(row) and row_time(row) >= start_time]

    bucket = defaultdict(list)
    for row in forward_rows:
        created = row_time(row)
        if not created:
            continue
        local_day = created.astimezone(tz).date()
        if local_day >= start_day:
            bucket[local_day].append(row)

    lines = []
    lines.append("DAILY FORWARD SUMMARY")
    lines.append("=" * 76)
    lines.append(f"timezone: Asia/Bangkok | days: {days}")
    if start_at:
        lines.append(f"start_at: {start_at}")
    lines.append("")
    lines.append(f"{'date':<12} {'signals':>7} {'win':>5} {'sl':>5} {'open':>6} {'timeout':>8} {'wr':>8} {'expR':>8} {'pf':>7}")

    total_rows = []
    for offset in range(days):
        day = start_day + timedelta(days=offset)
        day_rows = bucket.get(day, [])
        total_rows.extend(day_rows)
        lines.append(day_line(day, day_rows))

    lines.append("")
    lines.append("TOTAL")
    lines.append(summary_line(total_rows))
    lines.append("")
    lines.append("NEXT")
    if not total_rows:
        lines.append("- no forward signals in this period; keep Live running")
    else:
        lines.append("- keep collecting until 50-100 current-logic forward signals")
        lines.append("- keep execution state as configured: BTC demo auto guarded, XAU off unless explicitly changed")
    return "\n".join(lines)


def day_line(day, rows: list[dict]) -> str:
    wins, losses, open_rows, timeout_rows, win_rate, expectancy, pf = metrics(rows)
    return (
        f"{str(day):<12} {len(rows):>7} {wins:>5} {losses:>5} "
        f"{open_rows:>6} {timeout_rows:>8} {win_rate:>7.1f}% {expectancy:>8.3f} {pf:>7.2f}"
    )


def summary_line(rows: list[dict]) -> str:
    wins, losses, open_rows, timeout_rows, win_rate, expectancy, pf = metrics(rows)
    return (
        f"signals {len(rows)} | win {wins} | sl {losses} | open {open_rows} | "
        f"timeout {timeout_rows} | wr {win_rate:.1f}% | expectancy {expectancy:.3f}R | PF {pf:.2f}"
    )


def metrics(rows: list[dict]) -> tuple[int, int, int, int, float, float, float]:
    wins = len([row for row in rows if row.get("status") in ("tp", "tp1")])
    losses = len([row for row in rows if row.get("status") == "sl"])
    open_rows = len([row for row in rows if row.get("status") == "open"])
    timeout_rows = len([row for row in rows if row.get("status") == "timeout"])
    closed = wins + losses
    win_rate = wins / closed * 100 if closed else 0.0
    values = [r_multiple(row) for row in rows]
    values = [value for value in values if value is not None]
    expectancy = sum(values) / len(values) if values else 0.0
    gross_win = sum(value for value in values if value > 0)
    gross_loss = abs(sum(value for value in values if value < 0))
    pf = gross_win / gross_loss if gross_loss else 0.0
    return wins, losses, open_rows, timeout_rows, win_rate, expectancy, pf


def parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def row_time(row: dict) -> datetime | None:
    value = row.get("created_at")
    if not value:
        return None
    return parse_time(value)
