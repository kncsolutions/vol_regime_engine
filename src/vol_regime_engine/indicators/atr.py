# vol_regime_engine/indicators/atr.py

import pandas as pd
import numpy as np


class ATRCalculator:
    """
    Computes ATR (Average True Range) in points and percent.
    """

    def __init__(self, lookback: int = 14, method: str = "ema"):
        """
        Parameters:
        lookback : int
            Period for ATR calculation.
        method : str
            "ema" (default) or "sma"
        """
        self.lookback = lookback
        self.method = method.lower()

    # ---------------------------------------------------------
    # True Range
    # ---------------------------------------------------------

    @staticmethod
    def _true_range(df: pd.DataFrame) -> pd.Series:
        """
        Calculates True Range.
        Requires columns: ['high', 'low', 'close']
        """

        high_low = df["high"] - df["low"]
        high_prev_close = np.abs(df["high"] - df["close"].shift(1))
        low_prev_close = np.abs(df["low"] - df["close"].shift(1))

        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)

        return tr

    # ---------------------------------------------------------
    # ATR Core
    # ---------------------------------------------------------

    def compute_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Returns ATR in price units (points).
        """

        required_cols = {"high", "low", "close"}
        if not required_cols.issubset(df.columns):
            raise ValueError("DataFrame must contain high, low, close columns")

        tr = self._true_range(df)

        if self.method == "ema":
            atr = tr.ewm(span=self.lookback, adjust=False).mean()
        elif self.method == "sma":
            atr = tr.rolling(window=self.lookback).mean()
        else:
            raise ValueError("Method must be 'ema' or 'sma'")

        return atr

    # ---------------------------------------------------------
    # ATR %
    # ---------------------------------------------------------

    def compute_atr_pct(self, df: pd.DataFrame) -> pd.Series:
        """
        Returns ATR as percentage of close.
        """

        atr = self.compute_atr(df)

        atr_pct = (atr / df["close"]) * 100

        return atr_pct

    # ---------------------------------------------------------
    # Safe Latest Value
    # ---------------------------------------------------------

    def latest_atr_values(self, df: pd.DataFrame) -> dict:
        """
        Returns latest ATR and ATR% safely.
        """

        if len(df) < self.lookback + 1:
            return {
                "atr_points": 0.0,
                "atr_pct": 0.0
            }

        atr_series = self.compute_atr(df)
        atr_pct_series = (atr_series / df["close"]) * 100

        return {
            "atr_points": float(atr_series.iloc[-1]),
            "atr_pct": float(atr_pct_series.iloc[-1])
        }