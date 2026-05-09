def session_profile(session: str, config: dict) -> dict:
    profile = {
        "target_rr_mult": 1.0,
        "sl_atr_mult": 1.0,
        "max_hold_bars": config.get("backtest", {}).get("max_hold_bars", 48),
        "tp1_rr": 1.0,
        "move_be_at_rr": 1.0,
    }
    profile.update(config.get("session_profiles", {}).get(session, {}))
    return profile
