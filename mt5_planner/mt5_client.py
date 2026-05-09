import pandas as pd

from .mt5_runtime import initialize_mt5


TIMEFRAMES = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}


class MT5Client:
    def __init__(self):
        self.mt5 = None

    def connect(self) -> None:
        self.mt5 = initialize_mt5({})

    def get_rates(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        if self.mt5 is None:
            raise RuntimeError("MT5 is not connected")

        tf_name = TIMEFRAMES.get(timeframe.upper())
        if not tf_name:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        self.mt5.symbol_select(symbol, True)
        rates = self.mt5.copy_rates_from_pos(
            symbol,
            getattr(self.mt5, tf_name),
            0,
            bars,
        )
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"No MT5 rates for {symbol} {timeframe}: {self.mt5.last_error()}")

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df
