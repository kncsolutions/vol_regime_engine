def three_white_soldiers(df):
        return (df.dir > 0) & (df.shift(1).dir > 0) & (df.shift(2).dir > 0)

def three_black_crows(df):
    return (df.dir < 0) & (df.shift(1).dir < 0) & (df.shift(2).dir < 0)

def morning_star(df):
    c1, c2, c3 = df.shift(2), df.shift(1), df
    mid = (c1.open + c1.close) / 2
    return (c1.dir < 0) & (c2.body_pct < 0.3) & (c3.dir > 0) & (c3.close > mid)