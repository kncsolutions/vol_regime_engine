import os
from pathlib import Path
from textwrap import dedent

PROJECT_NAME = "candlestick_engine"
BASE_DIR = Path(PROJECT_NAME)


# --------------------------------------------------
# Utility
# --------------------------------------------------

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content.strip()))
    print(f"Created: {path}")


# --------------------------------------------------
# 1️⃣ Create Directory Structure
# --------------------------------------------------

folders = [
    BASE_DIR,
    BASE_DIR / PROJECT_NAME,
    BASE_DIR / PROJECT_NAME / "core",
    BASE_DIR / PROJECT_NAME / "patterns",
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2️⃣ pyproject.toml (PEP 621 - Modern Packaging)
# --------------------------------------------------

write_file(
    BASE_DIR / "pyproject.toml",
    """
    [build-system]
    requires = ["setuptools>=61.0"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "candlestick-engine"
    version = "0.1.0"
    description = "Vectorized Candlestick Pattern Detection Engine"
    authors = [{name = "Your Name"}]
    readme = "README.md"
    requires-python = ">=3.9"
    dependencies = [
        "pandas",
        "numpy"
    ]

    [tool.setuptools.packages.find]
    where = ["."]
    """
)

# --------------------------------------------------
# 3️⃣ README
# --------------------------------------------------

write_file(
    BASE_DIR / "README.md",
    """
    # Candlestick Engine

    Vectorized detection of 40 classical candlestick patterns.

    ## Installation

    pip install -e .

    ## Usage

    from candlestick_engine.engine import CandlestickEngine
    """
)

# --------------------------------------------------
# 4️⃣ __init__.py
# --------------------------------------------------

write_file(
    BASE_DIR / PROJECT_NAME / "__init__.py",
    """
    from .engine import CandlestickEngine
    """
)

# --------------------------------------------------
# 5️⃣ Core Features
# --------------------------------------------------

write_file(
    BASE_DIR / PROJECT_NAME / "core" / "features.py",
    """
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
    """
)

# --------------------------------------------------
# 6️⃣ Pattern Files
# --------------------------------------------------

write_file(
    BASE_DIR / PROJECT_NAME / "patterns" / "__init__.py",
    """
    from .registry import ALL_PATTERNS
    """
)

write_file(
    BASE_DIR / PROJECT_NAME / "patterns" / "single.py",
    """
    def hammer(df):
        return (df.lower_pct > 0.6) & (df.upper_pct < 0.2) & (df.body_pct < 0.35)

    def shooting_star(df):
        return (df.upper_pct > 0.6) & (df.lower_pct < 0.2) & (df.body_pct < 0.35)

    def doji(df):
        return df.body_pct < 0.1

    def bullish_marubozu(df):
        return (df.body_pct > 0.85) & (df.dir > 0)

    def bearish_marubozu(df):
        return (df.body_pct > 0.85) & (df.dir < 0)
    """
)

write_file(
    BASE_DIR / PROJECT_NAME / "patterns" / "double.py",
    """
    def bullish_engulfing(df):
        p = df.shift(1)
        return (p.dir < 0) & (df.dir > 0) & (df.open < p.close) & (df.close > p.open)

    def bearish_engulfing(df):
        p = df.shift(1)
        return (p.dir > 0) & (df.dir < 0) & (df.open > p.close) & (df.close < p.open)

    def inside_bar(df):
        p = df.shift(1)
        return (df.high < p.high) & (df.low > p.low)

    def outside_bar(df):
        p = df.shift(1)
        return (df.high > p.high) & (df.low < p.low)
    """
)

write_file(
    BASE_DIR / PROJECT_NAME / "patterns" / "triple.py",
    """
    def three_white_soldiers(df):
        return (df.dir > 0) & (df.shift(1).dir > 0) & (df.shift(2).dir > 0)

    def three_black_crows(df):
        return (df.dir < 0) & (df.shift(1).dir < 0) & (df.shift(2).dir < 0)

    def morning_star(df):
        c1, c2, c3 = df.shift(2), df.shift(1), df
        mid = (c1.open + c1.close) / 2
        return (c1.dir < 0) & (c2.body_pct < 0.3) & (c3.dir > 0) & (c3.close > mid)
    """
)

write_file(
    BASE_DIR / PROJECT_NAME / "patterns" / "registry.py",
    """
    from .single import *
    from .double import *
    from .triple import *

    ALL_PATTERNS = {
        "hammer": hammer,
        "shooting_star": shooting_star,
        "doji": doji,
        "bullish_marubozu": bullish_marubozu,
        "bearish_marubozu": bearish_marubozu,
        "bullish_engulfing": bullish_engulfing,
        "bearish_engulfing": bearish_engulfing,
        "inside_bar": inside_bar,
        "outside_bar": outside_bar,
        "three_white_soldiers": three_white_soldiers,
        "three_black_crows": three_black_crows,
        "morning_star": morning_star,
    }
    """
)

# --------------------------------------------------
# 7️⃣ Engine
# --------------------------------------------------

write_file(
    BASE_DIR / PROJECT_NAME / "engine.py",
    """
    import pandas as pd
    from .core.features import compute_features
    from .patterns.registry import ALL_PATTERNS

    class CandlestickEngine:

        def __init__(self, patterns=None):
            self.patterns = patterns or ALL_PATTERNS

        def run(self, df: pd.DataFrame):
            df = compute_features(df)

            results = {}
            for name, func in self.patterns.items():
                results[name] = func(df)

            return pd.DataFrame(results, index=df.index)
    """
)

print("\\nProject successfully created.")
print(f"Next steps:")
print(f"cd {PROJECT_NAME}")
print("pip install -e .")
