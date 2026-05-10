from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from .mt5_runtime import initialize_mt5


def ledger_path(config: dict) -> str:
    configured = config.get("order_ledger_path")
    if configured:
        return str(configured)
    symbol = str(config.get("symbol", "symbol")).lower()
    return f"orders_{symbol}_current.sqlite"


def sync_order_ledger(config: dict, start_at: str | None = None) -> str:
    path = ledger_path(config)
    init_ledger(path)
    mt5 = initialize_mt5(config)
    try:
        start = parse_time(start_at) or parse_time(config.get("report", {}).get("forward_start", ""))
        if start is None:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.now(timezone.utc)
        symbol = str(config.get("symbol") or "")
        magic = int(config.get("execution", {}).get("magic", 0) or 0)

        deals = mt5.history_deals_get(start, end) or []
        filtered_deals = [
            deal for deal in deals
            if getattr(deal, "symbol", "") == symbol
            and (not magic or int(getattr(deal, "magic", 0) or 0) == magic)
        ]
        positions = mt5.positions_get(symbol=symbol) or []
        filtered_positions = [
            position for position in positions
            if not magic or int(getattr(position, "magic", 0) or 0) == magic
        ]

        rows = build_order_rows(config, filtered_deals, filtered_positions)
        with sqlite3.connect(path) as conn:
            for row in rows:
                upsert_order(conn, row)
        return f"synced_orders: {len(rows)} | deals: {len(filtered_deals)} | open_positions: {len(filtered_positions)} | ledger: {path}"
    finally:
        mt5.shutdown()


def build_order_report(config: dict, start_at: str | None = None, limit: int = 10) -> str:
    path = ledger_path(config)
    init_ledger(path)
    start = parse_time(start_at) or parse_time(config.get("report", {}).get("forward_start", ""))
    rows = read_orders(path, start)
    lines = ["ACTUAL MT5 ORDER LEDGER", "=" * 72]
    lines.append(f"symbol: {config.get('symbol')} | ledger: {path}")
    if start:
        lines.append(f"start_at: {start.isoformat()}")
    if not rows:
        lines.append("no MT5 orders in ledger yet")
        lines.append("run order-sync while MT5 is open")
        return "\n".join(lines)

    closed = [row for row in rows if row["status"] == "closed"]
    open_rows = [row for row in rows if row["status"] == "open"]
    wins = [row for row in closed if float(row["net_profit"] or 0) > 0]
    losses = [row for row in closed if float(row["net_profit"] or 0) < 0]
    be = [row for row in closed if float(row["net_profit"] or 0) == 0]
    pnl = sum(float(row["net_profit"] or 0) for row in closed)
    open_pnl = sum(float(row["net_profit"] or 0) for row in open_rows)
    gross_win = sum(float(row["net_profit"] or 0) for row in wins)
    gross_loss = abs(sum(float(row["net_profit"] or 0) for row in losses))
    win_rate = len(wins) / (len(wins) + len(losses)) * 100 if wins or losses else 0
    profit_factor = gross_win / gross_loss if gross_loss else None

    lines.append(
        f"orders: {len(rows)} | closed {len(closed)} | open {len(open_rows)} | "
        f"wins {len(wins)} | losses {len(losses)} | be {len(be)} | WR {win_rate:.1f}%"
    )
    pf_text = f"{profit_factor:.2f}" if profit_factor is not None else "inf"
    lines.append(f"closed P/L: ${pnl:.2f} | open P/L: ${open_pnl:.2f} | marked total: ${pnl + open_pnl:.2f}")
    lines.append(f"gross win ${gross_win:.2f} | gross loss ${gross_loss:.2f} | PF {pf_text}")
    lines.append("")
    lines.append("RECENT MT5 ORDERS")
    lines.append(f"{'position':>12} {'side':<5} {'status':<7} {'vol':>6} {'entry':>10} {'sl':>10} {'tp':>10} {'p/l':>9}")
    for row in rows[-limit:]:
        lines.append(
            f"{int(row['position_id']):>12} {row['side']:<5} {row['status']:<7} "
            f"{float(row['volume'] or 0):>6.2f} {float(row['entry_price'] or 0):>10.3f} "
            f"{float(row['stop_loss'] or 0):>10.3f} {float(row['take_profit'] or 0):>10.3f} "
            f"{float(row['net_profit'] or 0):>9.2f}"
        )
    return "\n".join(lines)


def init_ledger(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            create table if not exists mt5_orders (
                position_id integer primary key,
                symbol text not null,
                magic integer,
                side text,
                status text not null,
                volume real,
                entry_price real,
                exit_price real,
                stop_loss real,
                take_profit real,
                open_time text,
                close_time text,
                profit real,
                swap real,
                commission real,
                net_profit real,
                comment text,
                deal_count integer,
                raw_json text,
                synced_at text not null
            )
            """
        )
        columns = [row[1] for row in conn.execute("pragma table_info(mt5_orders)")]
        if "stop_loss" not in columns:
            conn.execute("alter table mt5_orders add column stop_loss real")
        if "take_profit" not in columns:
            conn.execute("alter table mt5_orders add column take_profit real")


def build_order_rows(config: dict, deals, positions) -> list[dict]:
    symbol = str(config.get("symbol") or "")
    magic = int(config.get("execution", {}).get("magic", 0) or 0)
    grouped = defaultdict(list)
    for deal in deals:
        position_id = int(getattr(deal, "position_id", 0) or getattr(deal, "order", 0) or 0)
        if position_id:
            grouped[position_id].append(deal)

    rows = []
    for position_id, group in grouped.items():
        rows.append(row_from_deals(position_id, symbol, magic, group))

    known = {row["position_id"] for row in rows}
    for position in positions:
        position_id = int(getattr(position, "ticket", 0) or 0)
        if not position_id:
            continue
        row = row_from_position(position, symbol, magic)
        if position_id in known:
            rows = [merge_open_position(existing, row) if existing["position_id"] == position_id else existing for existing in rows]
        else:
            rows.append(row)
    return sorted(rows, key=lambda row: row.get("open_time") or "")


def row_from_deals(position_id: int, symbol: str, magic: int, deals) -> dict:
    sorted_deals = sorted(deals, key=lambda deal: int(getattr(deal, "time", 0) or 0))
    entry_deals = [deal for deal in sorted_deals if int(getattr(deal, "entry", 0) or 0) == 0]
    exit_deals = [deal for deal in sorted_deals if int(getattr(deal, "entry", 0) or 0) != 0]
    first = entry_deals[0] if entry_deals else sorted_deals[0]
    side = "BUY" if int(getattr(first, "type", 0) or 0) == 0 else "SELL"
    entry_volume = sum(float(getattr(deal, "volume", 0) or 0) for deal in entry_deals) or float(getattr(first, "volume", 0) or 0)
    exit_volume = sum(float(getattr(deal, "volume", 0) or 0) for deal in exit_deals)
    entry_price = weighted_price(entry_deals) or float(getattr(first, "price", 0) or 0)
    exit_price = weighted_price(exit_deals)
    profit = sum(float(getattr(deal, "profit", 0) or 0) for deal in sorted_deals)
    swap = sum(float(getattr(deal, "swap", 0) or 0) for deal in sorted_deals)
    commission = sum(float(getattr(deal, "commission", 0) or 0) for deal in sorted_deals)
    status = "closed" if exit_deals and exit_volume >= entry_volume else "open"
    close_time = deal_time(exit_deals[-1]) if exit_deals and status == "closed" else None
    return {
        "position_id": position_id,
        "symbol": symbol,
        "magic": magic,
        "side": side,
        "status": status,
        "volume": entry_volume,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_loss": None,
        "take_profit": None,
        "open_time": deal_time(first),
        "close_time": close_time,
        "profit": profit,
        "swap": swap,
        "commission": commission,
        "net_profit": profit + swap + commission,
        "comment": str(getattr(sorted_deals[-1], "comment", "") or ""),
        "deal_count": len(sorted_deals),
        "raw_json": json.dumps([deal_to_dict(deal) for deal in sorted_deals], ensure_ascii=False),
    }


def row_from_position(position, symbol: str, magic: int) -> dict:
    side = "BUY" if int(getattr(position, "type", 0) or 0) == 0 else "SELL"
    return {
        "position_id": int(getattr(position, "ticket", 0) or 0),
        "symbol": symbol,
        "magic": magic,
        "side": side,
        "status": "open",
        "volume": float(getattr(position, "volume", 0) or 0),
        "entry_price": float(getattr(position, "price_open", 0) or 0),
        "exit_price": None,
        "stop_loss": float(getattr(position, "sl", 0) or 0),
        "take_profit": float(getattr(position, "tp", 0) or 0),
        "open_time": seconds_to_iso(int(getattr(position, "time", 0) or 0)),
        "close_time": None,
        "profit": float(getattr(position, "profit", 0) or 0),
        "swap": float(getattr(position, "swap", 0) or 0),
        "commission": 0.0,
        "net_profit": float(getattr(position, "profit", 0) or 0) + float(getattr(position, "swap", 0) or 0),
        "comment": str(getattr(position, "comment", "") or ""),
        "deal_count": 0,
        "raw_json": json.dumps(position_to_dict(position), ensure_ascii=False),
    }


def merge_open_position(existing: dict, current: dict) -> dict:
    if existing["status"] == "closed":
        return existing
    merged = dict(existing)
    merged.update({
        "status": "open",
        "volume": current["volume"],
        "net_profit": current["net_profit"],
        "profit": current["profit"],
        "swap": current["swap"],
        "stop_loss": current["stop_loss"],
        "take_profit": current["take_profit"],
        "raw_json": current["raw_json"],
    })
    return merged


def upsert_order(conn, row: dict) -> None:
    row = dict(row)
    row["synced_at"] = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        insert into mt5_orders (
            position_id, symbol, magic, side, status, volume, entry_price, exit_price,
            stop_loss, take_profit, open_time, close_time, profit, swap, commission, net_profit, comment,
            deal_count, raw_json, synced_at
        ) values (
            :position_id, :symbol, :magic, :side, :status, :volume, :entry_price, :exit_price,
            :stop_loss, :take_profit, :open_time, :close_time, :profit, :swap, :commission, :net_profit, :comment,
            :deal_count, :raw_json, :synced_at
        )
        on conflict(position_id) do update set
            status = excluded.status,
            volume = excluded.volume,
            exit_price = excluded.exit_price,
            stop_loss = excluded.stop_loss,
            take_profit = excluded.take_profit,
            close_time = excluded.close_time,
            profit = excluded.profit,
            swap = excluded.swap,
            commission = excluded.commission,
            net_profit = excluded.net_profit,
            comment = excluded.comment,
            deal_count = excluded.deal_count,
            raw_json = excluded.raw_json,
            synced_at = excluded.synced_at
        """,
        row,
    )


def read_orders(path: str, start: datetime | None = None) -> list[sqlite3.Row]:
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        if start:
            rows = conn.execute(
                """
                select * from mt5_orders
                where open_time >= ? or close_time >= ?
                order by coalesce(open_time, close_time) asc
                """,
                (start.isoformat(), start.isoformat()),
            ).fetchall()
        else:
            rows = conn.execute("select * from mt5_orders order by coalesce(open_time, close_time) asc").fetchall()
    return rows


def weighted_price(deals) -> float | None:
    volume = sum(float(getattr(deal, "volume", 0) or 0) for deal in deals)
    if volume <= 0:
        return None
    return sum(float(getattr(deal, "price", 0) or 0) * float(getattr(deal, "volume", 0) or 0) for deal in deals) / volume


def deal_time(deal) -> str:
    return seconds_to_iso(int(getattr(deal, "time", 0) or 0))


def seconds_to_iso(value: int) -> str | None:
    if value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def deal_to_dict(deal) -> dict:
    return {
        "ticket": int(getattr(deal, "ticket", 0) or 0),
        "order": int(getattr(deal, "order", 0) or 0),
        "position_id": int(getattr(deal, "position_id", 0) or 0),
        "time": deal_time(deal),
        "type": int(getattr(deal, "type", 0) or 0),
        "entry": int(getattr(deal, "entry", 0) or 0),
        "volume": float(getattr(deal, "volume", 0) or 0),
        "price": float(getattr(deal, "price", 0) or 0),
        "profit": float(getattr(deal, "profit", 0) or 0),
        "swap": float(getattr(deal, "swap", 0) or 0),
        "commission": float(getattr(deal, "commission", 0) or 0),
        "comment": str(getattr(deal, "comment", "") or ""),
    }


def position_to_dict(position) -> dict:
    return {
        "ticket": int(getattr(position, "ticket", 0) or 0),
        "time": seconds_to_iso(int(getattr(position, "time", 0) or 0)),
        "type": int(getattr(position, "type", 0) or 0),
        "volume": float(getattr(position, "volume", 0) or 0),
        "price_open": float(getattr(position, "price_open", 0) or 0),
        "price_current": float(getattr(position, "price_current", 0) or 0),
        "sl": float(getattr(position, "sl", 0) or 0),
        "tp": float(getattr(position, "tp", 0) or 0),
        "profit": float(getattr(position, "profit", 0) or 0),
        "swap": float(getattr(position, "swap", 0) or 0),
        "comment": str(getattr(position, "comment", "") or ""),
    }
