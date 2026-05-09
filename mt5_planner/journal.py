import json
import sqlite3
from datetime import datetime, timedelta, timezone


class Journal:
    def __init__(self, path: str):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                create table if not exists signals (
                    id integer primary key autoincrement,
                    created_at text not null,
                    symbol text not null,
                    timeframe text not null,
                    mode text not null,
                    direction text not null,
                    entry real not null,
                    stop_loss real not null,
                    take_profit real not null,
                    risk_reward real not null,
                    unique_key text,
                    status text not null default 'open',
                    closed_at text,
                    close_price real,
                    quality_score integer,
                    quality_label text,
                    session text,
                    spread real,
                    lot real,
                    actual_risk_usd real,
                    idea_key text,
                    mfe real,
                    mae real,
                    source text,
                    payload text not null
                )
                """
            )
            columns = [row[1] for row in conn.execute("pragma table_info(signals)")]
            if "unique_key" not in columns:
                conn.execute("alter table signals add column unique_key text")
            if "status" not in columns:
                conn.execute("alter table signals add column status text not null default 'open'")
            if "closed_at" not in columns:
                conn.execute("alter table signals add column closed_at text")
            if "close_price" not in columns:
                conn.execute("alter table signals add column close_price real")
            if "quality_score" not in columns:
                conn.execute("alter table signals add column quality_score integer")
            if "quality_label" not in columns:
                conn.execute("alter table signals add column quality_label text")
            if "session" not in columns:
                conn.execute("alter table signals add column session text")
            if "spread" not in columns:
                conn.execute("alter table signals add column spread real")
            if "lot" not in columns:
                conn.execute("alter table signals add column lot real")
            if "actual_risk_usd" not in columns:
                conn.execute("alter table signals add column actual_risk_usd real")
            if "idea_key" not in columns:
                conn.execute("alter table signals add column idea_key text")
            if "mfe" not in columns:
                conn.execute("alter table signals add column mfe real")
            if "mae" not in columns:
                conn.execute("alter table signals add column mae real")
            if "source" not in columns:
                conn.execute("alter table signals add column source text")
            if "manual_status" not in columns:
                conn.execute("alter table signals add column manual_status text")
            if "manual_entry" not in columns:
                conn.execute("alter table signals add column manual_entry real")
            if "manual_exit" not in columns:
                conn.execute("alter table signals add column manual_exit real")
            if "manual_note" not in columns:
                conn.execute("alter table signals add column manual_note text")
            if "manual_updated_at" not in columns:
                conn.execute("alter table signals add column manual_updated_at text")
            conn.execute(
                """
                create unique index if not exists idx_signals_unique_key
                on signals(unique_key)
                """
            )

    def save_signal(self, symbol: str, timeframe: str, plan: dict) -> bool:
        unique_key = "|".join(
            [
                symbol,
                timeframe,
                str(plan.get("candle_time", "")),
                plan["mode"],
                plan["direction"],
                str(plan["entry"]),
                str(plan["stop_loss"]),
                str(plan["take_profit"]),
            ]
        )
        idea_key = plan.get("idea_key")
        duplicate_window_seconds = int(plan.get("duplicate_window_seconds", 0) or 0)
        now = datetime.now(timezone.utc)
        with sqlite3.connect(self.path) as conn:
            if idea_key and duplicate_window_seconds > 0:
                cutoff = (now - timedelta(seconds=duplicate_window_seconds)).isoformat()
                duplicate = conn.execute(
                    """
                    select id
                    from signals
                    where symbol = ?
                      and timeframe = ?
                      and idea_key = ?
                      and created_at >= ?
                      and status in ('open', 'sl', 'tp', 'tp1', 'be', 'timeout')
                    order by id desc
                    limit 1
                    """,
                    (symbol, timeframe, idea_key, cutoff),
                ).fetchone()
                if duplicate:
                    return False
            cursor = conn.execute(
                """
                insert or ignore into signals (
                    created_at, symbol, timeframe, mode, direction,
                    entry, stop_loss, take_profit, risk_reward, unique_key,
                    quality_score, quality_label, session, spread, lot,
                    actual_risk_usd, idea_key, source, payload
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now.isoformat(),
                    symbol,
                    timeframe,
                    plan["mode"],
                    plan["direction"],
                    plan["entry"],
                    plan["stop_loss"],
                    plan["take_profit"],
                    plan["risk_reward"],
                    unique_key,
                    plan.get("quality_score"),
                    plan.get("quality_label"),
                    plan.get("session"),
                    plan.get("spread"),
                    plan.get("lot"),
                    plan.get("actual_risk_usd"),
                    idea_key,
                    plan.get("source", "forward"),
                    json.dumps(plan),
                ),
            )
            return cursor.rowcount == 1

    def recent_signals(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                select created_at, symbol, timeframe, mode, direction,
                       entry, stop_loss, take_profit, risk_reward,
                       quality_label, quality_score, status
                from signals
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def open_signals(self) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                select id, created_at, symbol, timeframe, mode, direction,
                       entry, stop_loss, take_profit, risk_reward, payload
                from signals
                where status = 'open'
                order by id asc
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def update_results(self, updates: list[dict]) -> int:
        count = 0
        with sqlite3.connect(self.path) as conn:
            for update in updates:
                cursor = conn.execute(
                    update_sql(update),
                    update_values(update),
                )
                count += cursor.rowcount
        return count

    def stats(self) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                select
                    mode,
                    coalesce(session, '-') as session,
                    status,
                    count(*) as count
                from signals
                group by mode, session, status
                order by mode, session, status
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def all_signals(self) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                select
                    created_at, symbol, timeframe, mode, direction,
                    entry, stop_loss, take_profit, risk_reward,
                    quality_score, quality_label, session, spread, lot,
                    actual_risk_usd, idea_key, status, closed_at, close_price,
                    mfe, mae, source, manual_status, manual_entry,
                    manual_exit, manual_note, manual_updated_at, payload
                from signals
                order by id asc
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def manual_recent(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                select
                    id, created_at, symbol, timeframe, direction, entry,
                    stop_loss, take_profit, status, manual_status,
                    manual_entry, manual_exit, manual_note
                from signals
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_manual(
        self,
        signal_id: int,
        manual_status: str,
        manual_entry: float | None = None,
        manual_exit: float | None = None,
        manual_note: str | None = None,
    ) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """
                update signals
                set manual_status = ?,
                    manual_entry = ?,
                    manual_exit = ?,
                    manual_note = ?,
                    manual_updated_at = ?
                where id = ?
                """,
                (
                    manual_status,
                    manual_entry,
                    manual_exit,
                    manual_note,
                    datetime.now(timezone.utc).isoformat(),
                    signal_id,
                ),
            )
            return cursor.rowcount

    def clear_manual(self, signal_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """
                update signals
                set manual_status = null,
                    manual_entry = null,
                    manual_exit = null,
                    manual_note = null,
                    manual_updated_at = ?
                where id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), signal_id),
            )
            return cursor.rowcount


def update_sql(update: dict) -> str:
    if update["status"] == "open":
        return """
            update signals
            set mfe = ?, mae = ?
            where id = ? and status = 'open'
        """
    return """
        update signals
        set status = ?, closed_at = ?, close_price = ?, mfe = ?, mae = ?
        where id = ? and status = 'open'
    """


def update_values(update: dict) -> tuple:
    if update["status"] == "open":
        return (update.get("mfe"), update.get("mae"), update["id"])
    return (
        update["status"],
        update["closed_at"],
        update["close_price"],
        update.get("mfe"),
        update.get("mae"),
        update["id"],
    )
