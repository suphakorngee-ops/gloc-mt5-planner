from pathlib import Path


DEFAULT_TERMINAL_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"


def initialize_mt5(config: dict):
    import MetaTrader5 as mt5

    path = config.get("mt5_terminal_path") or default_terminal_path()
    ok = mt5.initialize(path=path) if path else mt5.initialize()
    if not ok:
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    return mt5


def default_terminal_path() -> str:
    return DEFAULT_TERMINAL_PATH if Path(DEFAULT_TERMINAL_PATH).exists() else ""
