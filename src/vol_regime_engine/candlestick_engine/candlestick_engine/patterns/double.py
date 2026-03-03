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