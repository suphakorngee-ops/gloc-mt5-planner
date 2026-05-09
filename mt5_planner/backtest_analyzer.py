import csv
from collections import defaultdict
from pathlib import Path


def analyze_backtest(path: str) -> str:
    rows = read_rows(path)
    if not rows:
        return "no backtest rows"

    lines = []
    lines.append(f"rows: {len(rows)}")
    lines.append("")
    lines.extend(section_status(rows))
    lines.append("")
    lines.extend(section_group(rows, "session"))
    lines.append("")
    lines.extend(section_group(rows, "setup"))
    lines.append("")
    lines.extend(section_group(rows, "fibo_zone"))
    lines.append("")
    lines.extend(section_mfe_mae(rows))
    lines.append("")
    lines.extend(section_expectancy(rows))
    lines.append("")
    lines.extend(section_suggestions(rows))
    return "\n".join(lines)


def read_rows(path: str) -> list[dict]:
    csv_path = Path(path)
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return []
    with csv_path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def section_status(rows: list[dict]) -> list[str]:
    counts = count_by(rows, "status")
    return [
        "STATUS",
        f"tp: {counts.get('tp', 0)}",
        f"tp1: {counts.get('tp1', 0)}",
        f"be: {counts.get('be', 0)}",
        f"sl: {counts.get('sl', 0)}",
        f"timeout: {counts.get('timeout', 0)}",
        f"ambiguous: {counts.get('ambiguous', 0)}",
    ]


def section_group(rows: list[dict], field: str) -> list[str]:
    grouped = defaultdict(lambda: {"tp": 0, "tp1": 0, "be": 0, "sl": 0, "timeout": 0, "ambiguous": 0})
    for row in rows:
        key = row.get(field) or "-"
        grouped[key][row.get("status") or "-"] += 1

    lines = [field.upper(), f"{field:<18} {'tp':>5} {'tp1':>5} {'be':>5} {'sl':>5} {'timeout':>8} {'wr':>8}"]
    for key, counts in sorted(grouped.items()):
        tp = counts.get("tp", 0) + counts.get("tp1", 0)
        sl = counts.get("sl", 0)
        closed = tp + sl
        wr = tp / closed * 100 if closed else 0
        lines.append(
            f"{key:<18} {counts.get('tp', 0):>5} {counts.get('tp1', 0):>5} "
            f"{counts.get('be', 0):>5} {sl:>5} {counts.get('timeout', 0):>8} {wr:>7.1f}%"
        )
    return lines


def section_mfe_mae(rows: list[dict]) -> list[str]:
    by_status = defaultdict(list)
    for row in rows:
        by_status[row.get("status")].append(row)

    lines = ["MFE/MAE"]
    for status in ["tp", "tp1", "be", "sl", "timeout"]:
        items = by_status.get(status, [])
        if not items:
            continue
        mfe = avg_float(items, "mfe")
        mae = avg_float(items, "mae")
        rr = avg_float(items, "risk_reward")
        lines.append(f"{status:<8} avg_mfe={mfe:.3f} avg_mae={mae:.3f} avg_rr={rr:.2f}")
    return lines


def section_expectancy(rows: list[dict]) -> list[str]:
    values = [r_multiple(row) for row in rows if r_multiple(row) is not None]
    if not values:
        return ["EXPECTANCY", "no R data"]

    wins = [value for value in values if value > 0]
    losses = [abs(value) for value in values if value < 0]
    breakeven = [value for value in values if value == 0]

    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    win_rate = len(wins) / len(values)
    loss_rate = len(losses) / len(values)
    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
    gross_win = sum(wins)
    gross_loss = sum(losses)
    profit_factor = gross_win / gross_loss if gross_loss else 0

    return [
        "EXPECTANCY",
        f"trades: {len(values)}",
        f"wins: {len(wins)} losses: {len(losses)} be/timeout: {len(breakeven)}",
        f"avg_win_R: {avg_win:.2f}",
        f"avg_loss_R: {avg_loss:.2f}",
        f"expectancy_R: {expectancy:.3f}",
        f"profit_factor: {profit_factor:.2f}",
    ]


def section_suggestions(rows: list[dict]) -> list[str]:
    sl_rows = [row for row in rows if row.get("status") == "sl"]
    timeout_rows = [row for row in rows if row.get("status") == "timeout"]
    tp_rows = [row for row in rows if row.get("status") in ("tp", "tp1")]

    lines = ["SUGGESTIONS"]
    vcp_rows = [row for row in rows if "vcp" in (row.get("setup") or "")]
    if vcp_rows:
        vcp_wins = len([row for row in vcp_rows if row.get("status") in ("tp", "tp1")])
        vcp_losses = len([row for row in vcp_rows if row.get("status") == "sl"])
        if vcp_wins > vcp_losses:
            lines.append("- VCP combinations show edge: prefer VCP + BOS/Fibo/SMC over plain fibo pullback")
    if len(sl_rows) > len(tp_rows) * 2:
        lines.append("- too many SL hits: tighten entry filter before changing lot")
    if timeout_rows:
        timeout_mfe = avg_float(timeout_rows, "mfe")
        timeout_mae = avg_float(timeout_rows, "mae")
        if timeout_mfe > timeout_mae:
            lines.append("- many timeouts move favorable first: consider closer TP or partial TP")
        else:
            lines.append("- timeouts do not move enough: wait for stronger momentum/confirmation")
    sl_mfe = avg_float(sl_rows, "mfe") if sl_rows else 0
    if sl_mfe > 0:
        lines.append(f"- SL trades still moved favorable avg {sl_mfe:.3f}: test TP1/BE management")
    lines.append("- keep mid/aggressive disabled until safe improves")
    return lines


def r_multiple(row: dict) -> float | None:
    try:
        entry = float(row.get("entry") or 0)
        stop = float(row.get("stop_loss") or 0)
        close_price = row.get("close_price")
        status = row.get("status")
        direction = row.get("direction")
    except ValueError:
        return None

    risk = abs(entry - stop)
    if risk <= 0:
        return None

    if status == "sl":
        return -1.0
    if status == "timeout":
        return 0.0
    if status == "be":
        return 0.0
    if close_price in (None, ""):
        return None

    try:
        close = float(close_price)
    except ValueError:
        return None

    if direction == "long":
        return (close - entry) / risk
    if direction == "short":
        return (entry - close) / risk
    return None


def count_by(rows: list[dict], field: str) -> dict:
    counts = defaultdict(int)
    for row in rows:
        counts[row.get(field) or "-"] += 1
    return dict(counts)


def avg_float(rows: list[dict], field: str) -> float:
    values = []
    for row in rows:
        try:
            value = float(row.get(field) or 0)
        except ValueError:
            value = 0
        values.append(value)
    return sum(values) / len(values) if values else 0
