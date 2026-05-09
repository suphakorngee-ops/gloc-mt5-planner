def apply_position_sizing(plan: dict, config: dict) -> dict:
    sizing = config.get("position_sizing", {})
    equity = float(config.get("account_equity", 1000))
    contract_size = float(sizing.get("contract_size", 100))
    fixed_lot = sizing.get("fixed_lot")
    min_lot = float(sizing.get("min_lot", 0.01))
    max_lot = float(sizing.get("max_lot", 100))
    lot_step = float(sizing.get("lot_step", 0.01))

    risk_pct = float(plan["risk_pct"])
    risk_usd = equity * risk_pct
    stop_distance = abs(float(plan["entry"]) - float(plan["stop_loss"]))
    raw_lot = risk_usd / (stop_distance * contract_size) if stop_distance > 0 else 0
    risk_note = "ok"
    if fixed_lot is not None:
        lot = float(fixed_lot)
        risk_note = "fixed_lot"
    else:
        lot = round_down_to_step(raw_lot, lot_step)
        if 0 < raw_lot < min_lot:
            lot = min_lot
            risk_note = "min_lot_exceeds_target_risk"
    lot = min(lot, max_lot)

    actual_risk_usd = stop_distance * contract_size * lot
    plan["risk_usd"] = round(risk_usd, 2)
    plan["lot"] = round(lot, 2)
    plan["actual_risk_usd"] = round(actual_risk_usd, 2)
    plan["stop_distance"] = round(stop_distance, 3)
    plan["risk_note"] = risk_note
    plan["risk_warning"] = risk_warning(actual_risk_usd, equity, config)
    return plan


def round_down_to_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return int(value / step) * step


def risk_warning(actual_risk_usd: float, equity: float, config: dict) -> str | None:
    guard = config.get("risk_guard", {})
    max_usd = guard.get("max_actual_risk_usd")
    max_pct = guard.get("max_actual_risk_pct")
    warnings = []
    if max_usd is not None and actual_risk_usd > float(max_usd):
        warnings.append(f"$risk {actual_risk_usd:.2f} > max ${float(max_usd):.2f}")
    if max_pct is not None and equity > 0:
        actual_pct = actual_risk_usd / equity
        if actual_pct > float(max_pct):
            warnings.append(f"risk {actual_pct:.2%} > max {float(max_pct):.2%}")
    return "; ".join(warnings) if warnings else None
