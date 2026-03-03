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