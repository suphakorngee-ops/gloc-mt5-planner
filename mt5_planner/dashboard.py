from html import escape
from pathlib import Path

from .forward_report import r_multiple


def build_dashboard(sections: list[dict], output: str = "reports/dashboard.html", refresh_seconds: int = 15) -> str:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    cards = "\n".join(render_section(section) for section in sections)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="{refresh_seconds}">
  <title>MT5 Planner Dashboard</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #0f172a; color: #e5e7eb; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    h1 {{ font-size: 28px; margin: 0 0 18px; }}
    h2 {{ font-size: 20px; margin: 0 0 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .card {{ background: #111827; border: 1px solid #263244; border-radius: 8px; padding: 16px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .metric {{ background: #0b1220; border-radius: 6px; padding: 10px; }}
    .label {{ color: #94a3b8; font-size: 12px; }}
    .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
    .good {{ color: #34d399; }}
    .bad {{ color: #fb7185; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #263244; padding: 8px; text-align: left; }}
    th {{ color: #94a3b8; font-weight: 600; }}
    .muted {{ color: #94a3b8; }}
  </style>
</head>
<body>
  <main>
    <h1>MT5 Planner Dashboard</h1>
    <p class="muted">Auto-refresh every {refresh_seconds}s. Re-run dashboard task to update from latest journal.</p>
    <div class="grid">
      {cards}
    </div>
  </main>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
    return str(path)


def render_section(section: dict) -> str:
    rows = section["rows"]
    metrics = compute_metrics(rows)
    recent_rows = rows[-8:]
    return f"""
<section class="card">
  <h2>{escape(section['name'])}</h2>
  <div class="metrics">
    {metric('Signals', metrics['signals'])}
    {metric('Progress', f"{metrics['signals']}/50")}
    {metric('Win Rate', f"{metrics['wr']:.1f}%", 'good' if metrics['wr'] >= 60 else '')}
    {metric('Expectancy', f"{metrics['expectancy']:.3f}R", 'good' if metrics['expectancy'] > 0 else 'bad')}
    {metric('Profit Factor', f"{metrics['pf']:.2f}", 'good' if metrics['pf'] >= 1.3 else '')}
    {metric('Open', metrics['open'])}
  </div>
  <table>
    <thead><tr><th>Time</th><th>Side</th><th>Paper</th><th>Manual</th><th>Entry</th><th>$Risk</th></tr></thead>
    <tbody>{''.join(render_row(row) for row in recent_rows) or '<tr><td colspan="5" class="muted">No forward signals yet</td></tr>'}</tbody>
  </table>
</section>
"""


def metric(label: str, value, cls: str = "") -> str:
    return f"""<div class="metric"><div class="label">{escape(label)}</div><div class="value {cls}">{escape(str(value))}</div></div>"""


def render_row(row: dict) -> str:
    created = escape(str(row.get("created_at", "-"))[:19])
    side = escape(str(row.get("direction", "-")))
    status = escape(str(row.get("status", "-")))
    manual = escape(str(row.get("manual_status") or "-"))
    entry = float(row.get("entry") or 0)
    risk = float(row.get("actual_risk_usd") or 0)
    return f"<tr><td>{created}</td><td>{side}</td><td>{status}</td><td>{manual}</td><td>{entry:.3f}</td><td>{risk:.2f}</td></tr>"


def compute_metrics(rows: list[dict]) -> dict:
    wins = len([row for row in rows if row.get("status") in ("tp", "tp1")])
    losses = len([row for row in rows if row.get("status") == "sl"])
    open_rows = len([row for row in rows if row.get("status") == "open"])
    closed = wins + losses
    values = [r_multiple(row) for row in rows]
    values = [value for value in values if value is not None]
    gross_win = sum(value for value in values if value > 0)
    gross_loss = abs(sum(value for value in values if value < 0))
    return {
        "signals": len(rows),
        "open": open_rows,
        "wr": wins / closed * 100 if closed else 0.0,
        "expectancy": sum(values) / len(values) if values else 0.0,
        "pf": gross_win / gross_loss if gross_loss else 0.0,
    }
