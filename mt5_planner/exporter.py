import csv
import json
from pathlib import Path


def export_signals(rows: list[dict], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "created_at",
        "symbol",
        "timeframe",
        "mode",
        "direction",
        "entry",
        "stop_loss",
        "take_profit",
        "risk_reward",
        "quality_score",
        "quality_label",
        "session",
        "spread",
        "lot",
        "actual_risk_usd",
        "status",
        "source",
        "closed_at",
        "close_price",
        "mfe",
        "mae",
        "setup",
        "scalp_momentum",
        "trend_strength",
        "smc_event",
        "smc_flow",
        "fvg_event",
        "order_block",
        "wyckoff_event",
        "fibo_zone",
        "fibo_retracement",
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(flatten_signal(row))

    return len(rows)


def export_rows(rows: list[dict], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return 0

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def flatten_signal(row: dict) -> dict:
    payload = json.loads(row.get("payload") or "{}")
    features = payload.get("features") or {}
    return {
        "created_at": row.get("created_at"),
        "symbol": row.get("symbol"),
        "timeframe": row.get("timeframe"),
        "mode": row.get("mode"),
        "direction": row.get("direction"),
        "entry": row.get("entry"),
        "stop_loss": row.get("stop_loss"),
        "take_profit": row.get("take_profit"),
        "risk_reward": row.get("risk_reward"),
        "quality_score": row.get("quality_score") or payload.get("quality_score"),
        "quality_label": row.get("quality_label") or payload.get("quality_label"),
        "session": row.get("session") or payload.get("session"),
        "spread": row.get("spread") or payload.get("spread"),
        "lot": row.get("lot") or payload.get("lot"),
        "actual_risk_usd": row.get("actual_risk_usd") or payload.get("actual_risk_usd"),
        "status": row.get("status"),
        "source": row.get("source") or payload.get("source"),
        "closed_at": row.get("closed_at"),
        "close_price": row.get("close_price"),
        "mfe": row.get("mfe"),
        "mae": row.get("mae"),
        "setup": payload.get("setup"),
        "scalp_momentum": nested(features, "scalp_momentum", "ok"),
        "trend_strength": nested(features, "trend_follow", "strength"),
        "smc_event": nested(features, "smc", "event"),
        "smc_flow": nested(features, "smc_flow", "event"),
        "fvg_event": nested(nested_dict(features, "smc_flow"), "fvg", "event"),
        "order_block": nested(nested_dict(features, "smc_flow"), "order_block", "event"),
        "wyckoff_event": nested(nested_dict(features, "smc_flow"), "wyckoff", "event"),
        "fibo_zone": nested(features, "fibo", "zone"),
        "fibo_retracement": nested(features, "fibo", "retracement"),
    }


def nested(data: dict, key: str, subkey: str):
    value = data.get(key)
    if isinstance(value, dict):
        return value.get(subkey)
    return None


def nested_dict(data: dict, key: str) -> dict:
    value = data.get(key)
    return value if isinstance(value, dict) else {}
