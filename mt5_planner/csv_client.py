from pathlib import Path

import pandas as pd


def get_rates_from_csv(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"])
    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "bid",
        "ask",
        "spread_price",
        "spread_points",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna().reset_index(drop=True)
