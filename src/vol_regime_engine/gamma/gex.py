def calculate_gex(df, lot_size):
    df["call_gex"] = df["gamma"] * df["call_oi"] * lot_size
    df["put_gex"] = df["gamma"] * df["put_oi"] * lot_size
    df["net_gex"] = df["call_gex"] - df["put_gex"]
    return df
