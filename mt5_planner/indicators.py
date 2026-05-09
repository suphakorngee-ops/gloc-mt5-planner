import pandas as pd


def add_indicators(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    data = df.copy()
    ema_fast = int(settings.get("ema_fast", 50))
    ema_slow = int(settings.get("ema_slow", 200))
    rsi_period = int(settings.get("rsi_period", 14))
    atr_period = int(settings.get("atr_period", 14))

    data["ema_fast"] = data["close"].ewm(span=ema_fast, adjust=False).mean()
    data["ema_slow"] = data["close"].ewm(span=ema_slow, adjust=False).mean()
    data["rsi"] = rsi(data["close"], rsi_period)
    data["atr"] = atr(data, atr_period)
    data["swing_high"] = data["high"].rolling(20).max()
    data["swing_low"] = data["low"].rolling(20).min()
    return data


def rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()
