def detect_convexity_traps(df):
    df = df.sort_values("strike")
    df["d_gex"] = df["net_gex"].diff()
    slope_thresh = df["d_gex"].abs().quantile(0.9)
    traps = df[
        (df["net_gex"].shift(1) * df["net_gex"] < 0) &
        (df["d_gex"].abs() >= slope_thresh)
    ]
    return traps
