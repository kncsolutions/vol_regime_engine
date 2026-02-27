def identify_gamma_flip(df):
    df = df.sort_values("strike")
    df["cum_gex"] = df["net_gex"].cumsum()
    flip = df[df["cum_gex"].shift(1) * df["cum_gex"] < 0]
    if not flip.empty:
        return flip.iloc[0]["strike"]
    return None
