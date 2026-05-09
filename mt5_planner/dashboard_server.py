import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .dashboard import compute_metrics
from .forward_report import group_trade_ideas, parse_time, row_time
from .journal import Journal
from .mt5_runtime import initialize_mt5


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MT5 Planner Live Dashboard</title>
  <style>
    body { margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #0b1020; color: #e5e7eb; }
    main { max-width: 1240px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0 0 6px; font-size: 28px; }
    h2 { margin: 0 0 12px; font-size: 20px; }
    .muted { color: #94a3b8; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 14px; margin-top: 18px; }
    .banner { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-top: 18px; }
    .card { background: #111827; border: 1px solid #263244; border-radius: 8px; padding: 16px; }
    .wide { grid-column: 1 / -1; }
    .metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .metric { background: #0b1220; border-radius: 6px; padding: 10px; }
    .label { color: #94a3b8; font-size: 12px; }
    .value { font-size: 22px; font-weight: 700; margin-top: 4px; }
    .good { color: #34d399; }
    .bad { color: #fb7185; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
    th, td { border-bottom: 1px solid #263244; padding: 8px; text-align: left; vertical-align: top; }
    th { color: #94a3b8; font-weight: 600; }
    button { background: #1f2937; color: #e5e7eb; border: 1px solid #334155; border-radius: 6px; padding: 5px 8px; margin: 2px; cursor: pointer; }
    button:hover { background: #334155; }
    .taken { color: #34d399; }
    .skipped, .missed { color: #fbbf24; }
    .watch { color: #60a5fa; }
    .pill { display: inline-block; border: 1px solid #334155; border-radius: 999px; padding: 3px 8px; font-size: 12px; }
    .on { color: #34d399; border-color: #14532d; background: #052e1a; }
    .off { color: #fbbf24; border-color: #713f12; background: #291505; }
    .danger { color: #fb7185; border-color: #7f1d1d; background: #2a0b12; }
  </style>
</head>
<body>
  <main>
    <h1>MT5 Planner Live Dashboard</h1>
    <div class="muted">Auto refreshes every 5 seconds. Separates paper ideas, real MT5 demo positions, and Vloc-managed orders.</div>
    <div id="banner" class="banner"></div>
    <div id="positions" class="grid"></div>
    <div id="app" class="grid"></div>
  </main>
  <script>
    async function loadData() {
      const response = await fetch('/api/data');
      const data = await response.json();
      document.getElementById('banner').innerHTML = data.sections.map(renderBanner).join('');
      document.getElementById('positions').innerHTML = data.sections.map(renderPositions).join('');
      document.getElementById('app').innerHTML = data.sections.map(renderSection).join('');
    }

    function renderBanner(section) {
      const e = section.execution;
      const cls = e.enabled ? 'on' : 'off';
      return `<div class="metric">
        <div class="label">${section.name}</div>
        <div class="value"><span class="pill ${cls}">${e.enabled ? 'DEMO AUTO ON' : 'EXECUTION OFF'}</span></div>
        <div class="muted">Vloc manager: ${e.manage_positions ? 'ON' : 'OFF'} | lot ${e.fixed_lot || '-'} | max open ${e.max_open_trades}</div>
      </div>`;
    }

    function renderPositions(section) {
      const rows = section.positions.map(renderPosition).join('') || '<tr><td colspan="10" class="muted">No MT5 open positions for this symbol</td></tr>';
      return `<section class="card wide">
        <h2>${section.name} MT5 Open Positions</h2>
        <table>
          <thead><tr><th>Ticket</th><th>Owner</th><th>Side</th><th>Lot</th><th>Entry</th><th>Now</th><th>R</th><th>P/L</th><th>SL</th><th>TP</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </section>`;
    }

    function renderPosition(row) {
      const ownerCls = row.owner === 'Vloc' ? 'on' : 'danger';
      return `<tr>
        <td>${row.ticket}</td>
        <td><span class="pill ${ownerCls}">${row.owner}</span></td>
        <td>${row.side}</td>
        <td>${Number(row.volume || 0).toFixed(2)}</td>
        <td>${Number(row.entry || 0).toFixed(3)}</td>
        <td>${Number(row.current || 0).toFixed(3)}</td>
        <td>${Number(row.current_r || 0).toFixed(2)}R</td>
        <td class="${row.profit >= 0 ? 'good' : 'bad'}">${Number(row.profit || 0).toFixed(2)}</td>
        <td>${Number(row.sl || 0).toFixed(3)}</td>
        <td>${Number(row.tp || 0).toFixed(3)}</td>
      </tr>`;
    }

    function renderSection(section) {
      const m = section.metrics;
      const rows = section.rows.map(renderRow).join('') || '<tr><td colspan="8" class="muted">No forward signals yet</td></tr>';
      return `<section class="card">
        <h2>${section.name} Trade Ideas</h2>
        <div class="metrics">
          ${metric('Ideas', m.ideas)}
          ${metric('Raw', m.signals)}
          ${metric('Progress', `${m.signals}/50`)}
          ${metric('Open', m.open)}
          ${metric('Win Rate', `${m.wr.toFixed(1)}%`, m.wr >= 60 ? 'good' : '')}
          ${metric('Expectancy', `${m.expectancy.toFixed(3)}R`, m.expectancy > 0 ? 'good' : 'bad')}
          ${metric('Profit Factor', m.pf.toFixed(2), m.pf >= 1.3 ? 'good' : '')}
        </div>
        <table>
          <thead><tr><th>ID</th><th>Time</th><th>Side</th><th>Paper</th><th>Manual</th><th>Entry</th><th>$Risk</th><th>Mark</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </section>`;
    }

    function metric(label, value, cls='') {
      return `<div class="metric"><div class="label">${label}</div><div class="value ${cls}">${value}</div></div>`;
    }

    function renderRow(row) {
      const manual = row.manual_status || '-';
      return `<tr>
        <td>${row.id}</td>
        <td>${String(row.created_at || '-').slice(0, 19)}</td>
        <td>${row.direction || '-'}</td>
        <td>${row.status || '-'}</td>
        <td class="${manual}">${manual}</td>
        <td>${Number(row.entry || 0).toFixed(3)}</td>
        <td>${Number(row.actual_risk_usd || 0).toFixed(2)}</td>
        <td>
          <button onclick="mark('${row.symbol_key}', ${row.id}, 'taken')">taken</button>
          <button onclick="mark('${row.symbol_key}', ${row.id}, 'skipped')">skipped</button>
          <button onclick="mark('${row.symbol_key}', ${row.id}, 'missed')">missed</button>
          <button onclick="mark('${row.symbol_key}', ${row.id}, 'watch')">watch</button>
          <button onclick="clearMark('${row.symbol_key}', ${row.id})">clear</button>
        </td>
      </tr>`;
    }

    async function mark(symbol, id, status) {
      if (!confirm(`Mark signal #${id} as ${status}?`)) return;
      await fetch('/api/mark', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({symbol, id, status})
      });
      await loadData();
    }

    async function clearMark(symbol, id) {
      if (!confirm(`Clear manual mark for signal #${id}?`)) return;
      await fetch('/api/clear-mark', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({symbol, id})
      });
      await loadData();
    }

    loadData();
    setInterval(loadData, 5000);
  </script>
</body>
</html>
"""


def serve_dashboard(configs: dict, host: str = "127.0.0.1", port: int = 8765) -> None:
    handler = make_handler(configs)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"dashboard live: http://{host}:{port}")
    server.serve_forever()


def make_handler(configs: dict):
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.respond_html(HTML)
                return
            if parsed.path == "/api/data":
                self.respond_json({"sections": build_sections(configs)})
                return
            self.send_error(404)

        def do_POST(self):
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if parsed.path == "/api/mark":
                self.handle_mark(payload)
                return
            if parsed.path == "/api/clear-mark":
                self.handle_clear_mark(payload)
                return
            self.send_error(404)

        def handle_mark(self, payload):
            symbol = payload.get("symbol")
            config = configs.get(symbol)
            if not config:
                self.send_error(400, "unknown symbol")
                return
            status = payload.get("status")
            if status not in {"taken", "skipped", "missed", "watch"}:
                self.send_error(400, "bad status")
                return
            Journal(config["journal_path"]).update_manual(int(payload["id"]), status)
            self.respond_json({"ok": True})

        def handle_clear_mark(self, payload):
            symbol = payload.get("symbol")
            config = configs.get(symbol)
            if not config:
                self.send_error(400, "unknown symbol")
                return
            Journal(config["journal_path"]).clear_manual(int(payload["id"]))
            self.respond_json({"ok": True})

        def respond_html(self, text: str):
            data = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def respond_json(self, obj):
            data = json.dumps(obj).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            return

    return DashboardHandler


def build_sections(configs: dict) -> list[dict]:
    sections = []
    for symbol_key, config in configs.items():
        rows = current_rows(config)
        for row in rows:
            row["symbol_key"] = symbol_key
        sections.append(
            {
                "name": f"{config['symbol']} {config['timeframe']}",
                "execution": execution_summary(config),
                "positions": mt5_positions(config),
                "metrics": compute_metrics(rows),
                "rows": group_trade_ideas(rows)[-12:],
            }
        )
    return sections


def current_rows(config: dict) -> list[dict]:
    rows = Journal(config["journal_path"]).all_signals()
    start_at = (config.get("report") or {}).get("forward_start")
    if start_at:
        start = parse_time(start_at)
        rows = [row for row in rows if row_time(row) and row_time(row) >= start]
    return rows


def execution_summary(config: dict) -> dict:
    execution = config.get("execution", {})
    return {
        "enabled": bool(execution.get("enabled", False)),
        "manage_positions": bool(execution.get("manage_positions", False)),
        "fixed_lot": config.get("position_sizing", {}).get("fixed_lot"),
        "max_open_trades": execution.get("max_open_trades", 1),
        "daily_max_loss_usd": execution.get("daily_max_loss_usd", 0),
    }


def mt5_positions(config: dict) -> list[dict]:
    try:
        mt5 = initialize_mt5(config)
        symbol = config["symbol"]
        magic = int(config.get("execution", {}).get("magic", 0) or 0)
        positions = mt5.positions_get(symbol=symbol) or []
        result = []
        for position in positions:
            is_buy = int(position.type) == mt5.POSITION_TYPE_BUY
            entry = float(position.price_open)
            current = float(position.price_current)
            sl = float(position.sl or 0)
            risk = abs(entry - sl) if sl else 0
            current_r = ((current - entry) / risk if is_buy else (entry - current) / risk) if risk > 0 else 0
            owner = "Vloc" if int(getattr(position, "magic", 0) or 0) == magic else "Manual"
            result.append(
                {
                    "ticket": int(position.ticket),
                    "owner": owner,
                    "side": "BUY" if is_buy else "SELL",
                    "volume": float(position.volume),
                    "entry": entry,
                    "current": current,
                    "current_r": round(current_r, 3),
                    "profit": float(position.profit),
                    "sl": sl,
                    "tp": float(position.tp or 0),
                    "magic": int(getattr(position, "magic", 0) or 0),
                }
            )
        return result
    except Exception as exc:
        return [{"ticket": 0, "owner": "MT5 unavailable", "side": str(exc), "volume": 0, "entry": 0, "current": 0, "current_r": 0, "profit": 0, "sl": 0, "tp": 0, "magic": 0}]
