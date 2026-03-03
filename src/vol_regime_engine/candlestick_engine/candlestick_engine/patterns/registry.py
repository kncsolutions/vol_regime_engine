# patterns/registry.py

from .single import *
from .double import *
from .triple import *

SINGLE_PATTERNS = {
    "hammer": hammer,
    "shooting_star": shooting_star,
    "doji": doji,
    "bullish_marubozu": bullish_marubozu,
    "bearish_marubozu": bearish_marubozu,
}

DOUBLE_PATTERNS = {
    "bullish_engulfing": bullish_engulfing,
    "bearish_engulfing": bearish_engulfing,
    "inside_bar": inside_bar,
    "outside_bar": outside_bar,
}

TRIPLE_PATTERNS = {
    "three_white_soldiers": three_white_soldiers,
    "three_black_crows": three_black_crows,
    "morning_star": morning_star,
}

ALL_PATTERNS = {
    **SINGLE_PATTERNS,
    **DOUBLE_PATTERNS,
    **TRIPLE_PATTERNS,
}