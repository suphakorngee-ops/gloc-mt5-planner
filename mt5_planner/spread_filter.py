def spread_status(df, config: dict) -> dict:
    settings = config.get("spread_filter", {})
    max_spread = float(settings.get("max_spread_price", 0))
    if "spread_price" not in df.columns or df["spread_price"].dropna().empty:
        return {"available": False, "ok": True, "spread": None, "reason": "spread unavailable"}

    spread = float(df["spread_price"].dropna().iloc[-1])
    ok = max_spread <= 0 or spread <= max_spread
    reason = "ok" if ok else f"spread too high: {spread:.3f} > {max_spread:.3f}"
    return {"available": True, "ok": ok, "spread": spread, "reason": reason}
