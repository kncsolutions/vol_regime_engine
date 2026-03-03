import pandas as pd
import numpy as np

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["range"] = df["high"] - df["low"]
    df["body"] = (df["close"] - df["open"]).abs()
    df["upper"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower"] = df[["open", "close"]].min(axis=1) - df["low"]

    df["body_pct"] = df["body"] / df["range"]
    df["upper_pct"] = df["upper"] / df["range"]
    df["lower_pct"] = df["lower"] / df["range"]

    df["dir"] = np.sign(df["close"] - df["open"])

    return df