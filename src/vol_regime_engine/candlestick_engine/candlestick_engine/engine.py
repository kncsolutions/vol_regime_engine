# engine.py

import pandas as pd
from .core.features import compute_features
from .patterns.registry import (
    SINGLE_PATTERNS,
    DOUBLE_PATTERNS,
    TRIPLE_PATTERNS,
)

class CandlestickEngine:

    def __init__(self):
        pass

    def _evaluate_patterns(self, df, pattern_dict):
        triggered = []

        for name, func in pattern_dict.items():
            signal = func(df)

            # Check last candle only
            if signal.iloc[-1]:
                triggered.append(name)

        return triggered

    def run(self, df: pd.DataFrame):

        df = compute_features(df)

        latest_single = self._evaluate_patterns(df, SINGLE_PATTERNS)
        latest_double = self._evaluate_patterns(df, DOUBLE_PATTERNS)
        latest_triple = self._evaluate_patterns(df, TRIPLE_PATTERNS)

        return {
            "latest_single": latest_single,
            "latest_double": latest_double,
            "latest_triple": latest_triple,
            "all_latest": latest_single + latest_double + latest_triple
        }