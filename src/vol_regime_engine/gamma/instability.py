def detect_instability(df, quantile=0.1):
    threshold = df["net_gex"].quantile(quantile)
    return df[df["net_gex"] <= threshold]
