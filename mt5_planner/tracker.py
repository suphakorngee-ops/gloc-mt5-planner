import json


def evaluate_open_signals(rows: list[dict], candles) -> list[dict]:
    updates = []
    if candles.empty:
        return updates

    candles = candles.sort_values("time").reset_index(drop=True)
    for row in rows:
        payload = json.loads(row["payload"])
        signal_time = payload.get("candle_time")
        if not signal_time:
            continue

        future = candles[candles["time"] > signal_time]
        if future.empty:
            continue

        result = first_hit(row, future)
        mfe_mae = mfe_mae_for_signal(row, future)
        if result:
            updates.append(
                {
                    "id": row["id"],
                    "status": result["status"],
                    "closed_at": str(result["time"]),
                    "close_price": result["price"],
                    "mfe": mfe_mae["mfe"],
                    "mae": mfe_mae["mae"],
                }
            )
        elif mfe_mae["mfe"] is not None:
            updates.append(
                {
                    "id": row["id"],
                    "status": "open",
                    "closed_at": None,
                    "close_price": None,
                    "mfe": mfe_mae["mfe"],
                    "mae": mfe_mae["mae"],
                }
            )
    return updates


def first_hit(row: dict, candles) -> dict | None:
    direction = row["direction"]
    entry = float(row["entry"])
    sl = float(row["stop_loss"])
    tp = float(row["take_profit"])
    payload = json.loads(row.get("payload") or "{}")
    tp1_rr = float(payload.get("tp1_rr") or 0)
    risk = abs(entry - sl)
    tp1 = None
    if risk > 0 and tp1_rr > 0:
        if direction == "long":
            tp1 = entry + risk * tp1_rr
        else:
            tp1 = entry - risk * tp1_rr

    for _, candle in candles.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if direction == "long":
            hit_sl = low <= sl
            hit_tp = high >= tp
            hit_tp1 = tp1 is not None and high >= tp1
        else:
            hit_sl = high >= sl
            hit_tp = low <= tp
            hit_tp1 = tp1 is not None and low <= tp1

        if hit_sl and (hit_tp or hit_tp1):
            return {"status": "ambiguous", "time": candle["time"], "price": float(candle["close"])}
        if hit_sl:
            return {"status": "sl", "time": candle["time"], "price": sl}
        if hit_tp1:
            return {"status": "tp1", "time": candle["time"], "price": round(tp1, 3)}
        if hit_tp:
            return {"status": "tp", "time": candle["time"], "price": tp}

    return None


def mfe_mae_for_signal(row: dict, candles) -> dict:
    if candles.empty:
        return {"mfe": None, "mae": None}

    entry = float(row["entry"])
    direction = row["direction"]

    if direction == "long":
        mfe = float(candles["high"].max()) - entry
        mae = entry - float(candles["low"].min())
    else:
        mfe = entry - float(candles["low"].min())
        mae = float(candles["high"].max()) - entry

    return {"mfe": round(max(mfe, 0), 3), "mae": round(max(mae, 0), 3)}
