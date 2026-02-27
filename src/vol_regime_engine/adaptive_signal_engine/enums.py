from enum import Enum


class Bias(Enum):
    TREND_LONG = "trend_long"
    TREND_SHORT = "trend_short"
    MEAN_REVERT = "mean_revert"
    BREAKOUT = "breakout"